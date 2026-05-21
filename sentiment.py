import json
import os
from datetime import datetime
from sentiment_analyzer import analyze_record
from sentiment_report import generate

SETTINGS_FILE = "sentiment_settings.json"


def load_or_empty(path):
    if not os.path.exists(path):
        return {"last_updated": None, "records": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_sentiments(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_folder(folder, reparse=False):
    with open(os.path.join(folder, "settings.json"), encoding="utf-8") as f:
        settings = json.load(f)

    name = settings.get("name", os.path.basename(folder).replace("_", " ").title())
    topics = settings.get("topics", {})
    if not topics:
        print(f"  [{name}] No topics defined in settings.json — skipping")
        return

    results_file = os.path.join(folder, settings.get("data_file", "data/results.json"))
    sentiment_file = os.path.join(folder, "data/sentiments.json")
    report_file = os.path.join(folder, "data/sentiment_report.html")

    if not os.path.exists(results_file):
        print(f"  [{name}] No results.json found — run main.py first")
        return

    with open(results_file, encoding="utf-8") as f:
        results = json.load(f)

    sentiment_data = load_or_empty(sentiment_file)

    if reparse:
        sentiment_data["records"] = []
        print(f"  [{name}] Reparsing all records...")

    seen_ids = {r["id"] for r in sentiment_data["records"]}
    new_count = 0

    for record in results.get("records", []):
        if record["id"] in seen_ids:
            continue
        topic_sentiments = analyze_record(record, topics)
        if not topic_sentiments:
            continue
        sentiment_data["records"].append({
            "id": record["id"],
            "user_id": record.get("user_id", ""),
            "post_url": record.get("post_url", ""),
            "text_snippet": record.get("text_snippet", ""),
            "topics": topic_sentiments,
        })
        new_count += 1

    save_sentiments(sentiment_file, sentiment_data)
    generate(sentiment_data, report_file, title=name)
    print(f"  [{name}] {new_count} new records tagged — {len(sentiment_data['records'])} total")


def run(reparse=False):
    with open(SETTINGS_FILE, encoding="utf-8") as f:
        settings = json.load(f)

    folders = settings.get("folders", [])
    if not folders:
        print("No folders in sentiment_settings.json")
        return

    print(f"Running sentiment analysis on {len(folders)} folder(s)...")
    for folder in folders:
        run_folder(folder, reparse=reparse)


if __name__ == "__main__":
    import sys
    reparse = "--reparse" in sys.argv
    run(reparse=reparse)
