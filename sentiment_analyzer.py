import re
from collections import defaultdict

SENTIMENT_LEVELS = ["Excellent", "Good", "Neutral", "Bad", "Worst"]


def _score(pos, neg):
    if pos == 0 and neg == 0:
        return "Neutral"
    if pos >= 2 and neg == 0:
        return "Excellent"
    if pos >= 1 and neg == 0:
        return "Good"
    if neg >= 2 and pos == 0:
        return "Worst"
    if neg >= 1 and pos == 0:
        return "Bad"
    if pos > neg:
        return "Good"
    if neg > pos:
        return "Bad"
    return "Neutral"


def analyze_record(record, topics):
    text = (record.get("text") or record.get("text_snippet") or "").lower()
    if not text.strip():
        return {}

    result = {}
    for topic, config in topics.items():
        keywords = config.get("keywords", [])
        if not any(re.search(k, text) for k in keywords):
            continue

        pos = sum(1 for p in config.get("positive", []) if re.search(p, text))
        neg = sum(1 for n in config.get("negative", []) if re.search(n, text))
        result[topic] = _score(pos, neg)

    return result


def aggregate(sentiment_records, topics):
    """Return {topic: Counter({sentiment: count})} across all records."""
    agg = {t: defaultdict(int) for t in topics}
    for r in sentiment_records:
        for topic, sentiment in r.get("topics", {}).items():
            if topic in agg:
                agg[topic][sentiment] += 1
    return agg
