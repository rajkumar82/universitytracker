import re


def _match(text, keyword_map):
    text_lower = text.lower()
    for label, patterns in keyword_map.items():
        for p in patterns:
            if re.search(p, text_lower):
                return label
    return None


def parse(record, keywords):
    text = record.get("text") or record.get("text_snippet") or ""
    return {
        "id": record["id"],
        "user_id": record["user_id"],
        "post_url": record.get("post_url", ""),
        "source_url": record["source_url"],
        "created_at": record.get("created_at", ""),
        "scraped_at": record.get("scraped_at", ""),
        "text": text,
        "text_snippet": text[:300],
        "pillar": _match(text, keywords.get("pillars", {})),
        "scholarship": _match(text, keywords.get("scholarships", {})),
        "nationality": _match(text, keywords.get("nationalities", {})),
        "status": _match(text, keywords.get("statuses", {})),
    }
