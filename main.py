import json
import os
import sys
from datetime import datetime
from scraper import fetch
from parser import parse
from storage import load, save, merge, mark_thread_scraped
from summary import print_summary
from report import generate
from sentiment_analyzer import analyze_record
from sentiment_report import generate as generate_sentiment

OUTER_SETTINGS = "settings.json"
REPARSE = "--reparse" in sys.argv


def load_outer():
    with open(OUTER_SETTINGS, "r", encoding="utf-8") as f:
        return json.load(f)


def load_sentiments(path):
    if not os.path.exists(path):
        return {"last_updated": None, "records": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_sentiments(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_folder(folder):
    inner_path = os.path.join(folder, "settings.json")
    with open(inner_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    urls = settings["urls"]
    max_age_days = settings.get("max_age_days", 60)
    title = settings.get("name", os.path.basename(folder).replace("_", " ").title())
    data_file = os.path.join(folder, settings.get("data_file", "data/results.json"))
    report_file = os.path.join(folder, settings.get("report_file", "data/report.html"))
    sentiment_file = os.path.join(folder, "data/sentiments.json")
    sentiment_report_file = os.path.join(folder, "data/sentiment_report.html")

    keywords = settings.get("keywords", {})
    topics = settings.get("topics", {})

    print(f"\n{'='*55}")
    print(f"Folder  : {folder}  |  {len(urls)} URL(s)  |  max {max_age_days}d")
    print(f"{'='*55}")

    data = load(data_file)
    sentiment_data = load_sentiments(sentiment_file)
    scraped_threads = set(data.get("scraped_threads", []))
    total_added = 0
    sentiment_added = 0

    # reparse all existing records on --reparse
    if REPARSE:
        print(f"  Reparsing {len(data['records'])} existing records...")
        for r in data["records"]:
            updated = parse(r, keywords)
            r["pillar"] = updated["pillar"]
            r["scholarship"] = updated["scholarship"]
            r["nationality"] = updated["nationality"]
            r["status"] = updated["status"]
        save(data_file, data)
        sentiment_data["records"] = []
        print(f"  Reparse done.")
    elif data["records"] and keywords:
        # always reparse to pick up keyword changes
        for r in data["records"]:
            updated = parse(r, keywords)
            r["pillar"] = updated["pillar"]
            r["scholarship"] = updated["scholarship"]
            r["nationality"] = updated["nationality"]
            r["status"] = updated["status"]
        save(data_file, data)

    sentiment_seen = {r["id"] for r in sentiment_data["records"]}

    def on_thread_done(thread_url, raw_records):
        nonlocal total_added, sentiment_added, sentiment_seen

        # parse admission fields
        parsed = [parse(r, keywords) for r in raw_records if r.get("text", "").strip()]
        added = merge(data, parsed)
        mark_thread_scraped(data, thread_url)
        save(data_file, data)

        # sentiment analysis on same batch
        if topics:
            for r in parsed:
                if r["id"] in sentiment_seen:
                    continue
                tagged = analyze_record(r, topics)
                if tagged:
                    sentiment_data["records"].append({
                        "id": r["id"],
                        "user_id": r.get("user_id", ""),
                        "post_url": r.get("post_url", ""),
                        "text_snippet": r.get("text_snippet", ""),
                        "topics": tagged,
                    })
                    sentiment_seen.add(r["id"])
                    sentiment_added += 1
            save_sentiments(sentiment_file, sentiment_data)
            generate_sentiment(sentiment_data, sentiment_report_file, title=title)

        generate(data, report_file, title=title)
        total_added += added
        print(f"    saved {added} record(s) | {sentiment_added} sentiment tags — {len(data['records'])} total")

    for url in urls:
        print(f"\nFetching: {url}")
        try:
            fetch(
                url,
                max_age_days=max_age_days,
                scraped_threads=scraped_threads,
                on_thread_done=on_thread_done,
            )
        except Exception as e:
            print(f"  ! Error: {e}")

    # final reports
    generate(data, report_file, title=title)
    if topics:
        generate_sentiment(sentiment_data, sentiment_report_file, title=title)

    print(f"\nDone — {total_added} new record(s), {sentiment_added} sentiment tags")
    print_summary(data["records"], total_added)


def run():
    outer = load_outer()
    folders = outer.get("folders", [])
    if not folders:
        print("No folders configured in settings.json")
        return
    for folder in folders:
        run_folder(folder)


if __name__ == "__main__":
    run()
