import re

SENTIMENT_LEVELS = ["Excellent", "Good", "Neutral", "Bad", "Worst"]
DEFAULT_PROXIMITY = 80  # characters around keyword match to look for sentiment signals


def _score(pos, neg):
    if pos == 0 and neg == 0:
        return None  # no sentiment detected nearby — skip
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


def _find_match_positions(text, patterns):
    """Return list of (start, end) for all keyword matches."""
    positions = []
    for p in patterns:
        for m in re.finditer(p, text):
            positions.append((m.start(), m.end()))
    return positions


def analyze_record(record, topics):
    text = (record.get("text") or record.get("text_snippet") or "").lower()
    if not text.strip():
        return {}

    result = {}
    for topic, config in topics.items():
        keywords = config.get("keywords", [])
        positive = config.get("positive", [])
        negative = config.get("negative", [])
        proximity = config.get("proximity", DEFAULT_PROXIMITY)

        # find all positions where topic keyword appears
        match_positions = _find_match_positions(text, keywords)
        if not match_positions:
            continue

        # for each keyword match, check proximity window for sentiment signals
        total_pos = 0
        total_neg = 0
        for start, end in match_positions:
            window_start = max(0, start - proximity)
            window_end = min(len(text), end + proximity)
            window = text[window_start:window_end]

            total_pos += sum(1 for p in positive if re.search(p, window))
            total_neg += sum(1 for n in negative if re.search(n, window))

        sentiment = _score(total_pos, total_neg)
        if sentiment is not None:
            result[topic] = sentiment

    return result
