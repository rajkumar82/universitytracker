"""
Reparse sentiment from existing results.json without scraping.
Usage:
    python reparse_sentiment.py              # all folders
    python reparse_sentiment.py sutd         # specific folder name
"""
import json
import os
import sys
from datetime import datetime
from sentiment_analyzer import analyze_record
from sentiment_report import generate as generate_sentiment

OUTER_SETTINGS = "settings.json"


def reparse_folder(folder):
    inner_path = os.path.join(folder, "settings.json")
    with open(inner_path, encoding="utf-8") as f:
        settings = json.load(f)

    title = settings.get("name", os.path.basename(folder).replace("_", " ").title())
    topics = settings.get("topics", {})
    results_file = os.path.join(folder, settings.get("data_file", "data/results.json"))
    sentiment_file = os.path.join(folder, "data/sentiments.json")
    report_file = os.path.join(folder, "data/sentiment_report.html")

    if not topics:
        print(f"  [{title}] No topics in settings.json — skipping")
        return

    if not os.path.exists(results_file):
        print(f"  [{title}] No results.json found — run main.py first")
        return

    with open(results_file, encoding="utf-8") as f:
        results = json.load(f)

    records = results.get("records", [])
    print(f"  [{title}] Reparsing {len(records)} records...")

    tagged = []
    for r in records:
        result = analyze_record(r, topics)
        if not result:
            continue
        tagged.append({
            "id": r["id"],
            "user_id": r.get("user_id", ""),
            "post_url": r.get("post_url", ""),
            "text_snippet": r.get("text_snippet", ""),
            "topics": result,
        })

    sentiment_data = {
        "last_updated": datetime.utcnow().isoformat(),
        "records": tagged,
    }

    os.makedirs(os.path.dirname(sentiment_file), exist_ok=True)
    with open(sentiment_file, "w", encoding="utf-8") as f:
        json.dump(sentiment_data, f, indent=2, ensure_ascii=False)

    generate_sentiment(sentiment_data, report_file, title=title)
    print(f"  [{title}] Done — {len(tagged)} records tagged, report saved")


def run():
    with open(OUTER_SETTINGS, encoding="utf-8") as f:
        outer = json.load(f)

    all_folders = outer.get("folders", [])
    filter_name = sys.argv[1].lower() if len(sys.argv) > 1 else None

    folders = [
        f for f in all_folders
        if not filter_name or os.path.basename(f).lower() == filter_name
    ]

    if not folders:
        print(f"No matching folders for '{filter_name}'. Available: {[os.path.basename(f) for f in all_folders]}")
        return

    print(f"Reparsing sentiment for {len(folders)} folder(s)...")
    for folder in folders:
        reparse_folder(folder)


if __name__ == "__main__":
    run()
