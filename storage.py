import json
import os
from datetime import datetime


def load(path):
    if not os.path.exists(path):
        return {"last_updated": None, "scraped_threads": [], "records": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # backfill key for older results files
    data.setdefault("scraped_threads", [])
    return data


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge(data, new_records):
    seen_ids = {r["id"] for r in data["records"]}
    added = 0
    for rec in new_records:
        if rec["id"] not in seen_ids:
            rec["scraped_at"] = datetime.utcnow().isoformat()
            data["records"].append(rec)
            seen_ids.add(rec["id"])
            added += 1
    return added


def mark_thread_scraped(data, thread_url):
    if thread_url not in data["scraped_threads"]:
        data["scraped_threads"].append(thread_url)


def is_thread_scraped(data, thread_url):
    return thread_url in data["scraped_threads"]
