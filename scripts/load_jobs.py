import hashlib
import html
import re

YEARS_RE = re.compile(r"(\d+)(?:\s*[-–]\s*\d+)?\+?\s*years?", re.IGNORECASE)


def html_to_text(raw):
    text = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(text))


def extract_min_years(text):
    match = YEARS_RE.search(text)
    return int(match.group(1)) if match else None


def comeet_description(details):
    return "".join(f"<h3>{s['name']}</h3>{s['value']}" for s in details or [] if s["value"])


def make_content_hash(row):
    parts = [row["title"], row["city"], row["description"]]
    text = "|".join(str(p) for p in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
