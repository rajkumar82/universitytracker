import json
import os
from scraper import fetch
from parser import parse
from storage import load, save, merge, mark_thread_scraped, is_thread_scraped
from summary import print_summary
from report import generate

OUTER_SETTINGS = "settings.json"


def load_outer():
    with open(OUTER_SETTINGS, "r", encoding="utf-8") as f:
        return json.load(f)


def run_folder(folder):
    inner_path = os.path.join(folder, "settings.json")
    with open(inner_path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    urls = settings["urls"]
    max_age_days = settings.get("max_age_days", 60)
    data_file = os.path.join(folder, settings.get("data_file", "data/results.json"))
    report_file = os.path.join(folder, settings.get("report_file", "data/report.html"))

    print(f"\n{'='*55}")
    print(f"Folder  : {folder}  |  {len(urls)} URL(s)  |  max {max_age_days}d")
    print(f"{'='*55}")

    data = load(data_file)
    scraped_threads = set(data.get("scraped_threads", []))
    total_added = 0

    keywords = settings.get("keywords", {})

    def on_thread_done(thread_url, raw_records):
        nonlocal total_added
        parsed = [parse(r, keywords) for r in raw_records if r.get("text", "").strip()]
        added = merge(data, parsed)
        mark_thread_scraped(data, thread_url)
        save(data_file, data)
        generate(data, report_file)
        total_added += added
        print(f"    saved {added} new record(s) — {len(data['records'])} total")

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

    print(f"\nDone — {total_added} new record(s) added")
    print_summary(data["records"], total_added)
    generate(data, report_file)
    print(f"Report → {report_file}")


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
