from collections import Counter


def _count(records, field):
    values = [r[field] for r in records if r.get(field)]
    return Counter(values)


def print_summary(records, newly_added):
    total = len(records)
    print("\n" + "=" * 50)
    print("SUTD ADMISSION TRACKER — SUMMARY")
    print("=" * 50)
    print(f"Total records     : {total}")
    print(f"New this run      : {newly_added}")

    for field, label in [
        ("status", "Status"),
        ("pillar", "Pillar"),
        ("scholarship", "Scholarship"),
        ("nationality", "Nationality"),
    ]:
        counts = _count(records, field)
        if counts:
            print(f"\n{label}:")
            for k, v in counts.most_common():
                pct = v / total * 100
                print(f"  {k:<20} {v:>4}  ({pct:.1f}%)")

    no_data = [r for r in records if not any(r.get(f) for f in ["status", "pillar", "scholarship", "nationality"])]
    print(f"\nRecords with no extracted data: {len(no_data)}")
    print("=" * 50)
