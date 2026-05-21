import requests
import time
from datetime import datetime, timedelta, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def _get(url, params=None, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"  Rate limited — waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            time.sleep(2)
            return resp.json()
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            time.sleep(5)
    return None


def _cutoff_ts(max_age_days):
    return (datetime.now(timezone.utc) - timedelta(days=max_age_days)).timestamp()


def _is_thread_url(url):
    return "/comments/" in url


def fetch_thread(url, cutoff=None):
    """Fetch a specific thread and all its comments. Returns (thread_url, records)."""
    json_url = url.rstrip("/") + ".json"
    data = _get(json_url, params={"limit": 500})
    if not data:
        return url, []

    post = data[0]["data"]["children"][0]["data"]
    if cutoff and post.get("created_utc", 0) < cutoff:
        return url, []

    post_permalink = "https://www.reddit.com" + post.get("permalink", "")
    post_created = datetime.fromtimestamp(
        post.get("created_utc", 0), tz=timezone.utc
    ).isoformat()

    records = [{
        "id": "post_" + post["id"],
        "user_id": post.get("author", "[deleted]"),
        "text": (post.get("selftext") or post.get("title") or "").strip(),
        "source_url": url,
        "post_url": post_permalink,
        "created_at": post_created,
    }]

    for c in data[1]["data"]["children"]:
        if c["kind"] != "t1":
            continue
        d = c["data"]
        records.append({
            "id": "comment_" + d["id"],
            "user_id": d.get("author", "[deleted]"),
            "text": (d.get("body") or "").strip(),
            "source_url": url,
            "post_url": post_permalink,
            "created_at": datetime.fromtimestamp(
                d.get("created_utc", 0), tz=timezone.utc
            ).isoformat(),
        })
    return post_permalink, records


def fetch_subreddit_new(url, max_age_days=60, scraped_threads=None, on_thread_done=None):
    """Fetch all posts from /new, skipping already-scraped threads.
    Calls on_thread_done(thread_url, records) after each thread so the caller
    can save incrementally."""
    scraped_threads = scraped_threads or set()
    base = url.rstrip("/")
    cutoff = _cutoff_ts(max_age_days)
    after = None
    page = 0

    while True:
        params = {"limit": 100}
        if after:
            params["after"] = after

        data = _get(f"{base}/new.json", params=params)
        if not data:
            break

        children = data["data"]["children"]
        if not children:
            break

        page += 1
        stop = False
        for child in children:
            post = child["data"]
            created = post.get("created_utc", 0)
            if created < cutoff:
                stop = True
                break

            post_url = "https://www.reddit.com" + post["permalink"]
            if post_url in scraped_threads:
                print(f"  [skip] {post.get('title','')[:70]!r}")
                continue

            age_days = (datetime.now(timezone.utc).timestamp() - created) / 86400
            print(f"  [p{page}] {post.get('title','')[:70]!r} ({age_days:.0f}d ago)")

            thread_url, records = fetch_thread(post_url, cutoff=cutoff)
            if on_thread_done:
                on_thread_done(thread_url, records)

        if stop:
            print(f"  Reached posts older than {max_age_days} days — done.")
            break

        after = data["data"].get("after")
        if not after:
            break


def fetch(url, max_age_days=60, scraped_threads=None, on_thread_done=None):
    if _is_thread_url(url):
        cutoff = _cutoff_ts(max_age_days)
        thread_url, records = fetch_thread(url, cutoff=cutoff)
        if on_thread_done:
            on_thread_done(thread_url, records)
    else:
        fetch_subreddit_new(
            url,
            max_age_days=max_age_days,
            scraped_threads=scraped_threads,
            on_thread_done=on_thread_done,
        )
