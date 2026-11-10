import hashlib
import html
import json
import os
import re
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

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

def normalize_greenhouse(raw_jobs, company_id):
    jobs = pd.json_normalize(raw_jobs)
    jobs = jobs[jobs["location.name"].str.contains("Israel", na=False)]
    description = jobs["content"].apply(html.unescape)

    return pd.DataFrame({
        "ats_type": "greenhouse",
        "company_id": company_id,
        "external_id": jobs["id"].astype(str),
        "title": jobs["title"],
        "city": jobs["location.name"].str.split(",").str[0].str.strip(),
        "level": None,
        "work_mode": None,
        "min_years_experience": description.apply(html_to_text).apply(extract_min_years).astype("Int64"),
        "url": jobs["absolute_url"],
        "description": description,
    })


def normalize_comeet(raw_jobs, company_id):
    jobs = pd.json_normalize(raw_jobs)
    jobs = jobs[jobs["location.country"] == "IL"]
    description = jobs["custom_fields.details"].apply(comeet_description)

    return pd.DataFrame({
        "ats_type": "comeet",
        "company_id": company_id,
        "external_id": jobs["uid"],
        "title": jobs["name"],
        "city": jobs["location.city"],
        "level": jobs["experience_level"],
        "work_mode": jobs["workplace_type"],
        "min_years_experience": description.apply(html_to_text).apply(extract_min_years).astype("Int64"),
        "url": jobs["url_active_page"],
        "description": description,
    })

def add_job_id_and_hash(jobs):
    jobs = jobs.copy()
    jobs["job_id"] = jobs["ats_type"] + ":" + jobs["company_id"] + ":" + jobs["external_id"]
    jobs["content_hash"] = jobs.apply(make_content_hash, axis=1)
    return jobs


def save_jobs(jobs):
    records = jobs.astype(object).where(jobs.notna(), None).to_dict("records")
    inserted = 0

    with psycopg.connect(
       host=os.environ.get("POSTGRES_HOST", "localhost"),

        port=5432,
        user="noam",
        password=os.environ["POSTGRES_PASSWORD"],
        dbname="jobradar",
    ) as conn:
        for job in records:
            cur = conn.execute(
                """
                INSERT INTO job_postings (job_id, company_id, ats_type, external_id, title, level,
                                          city, work_mode, url, description, min_years_experience,
                                          content_hash)
                VALUES (%(job_id)s, %(company_id)s, %(ats_type)s, %(external_id)s, %(title)s, %(level)s,
                        %(city)s, %(work_mode)s, %(url)s, %(description)s, %(min_years_experience)s,
                        %(content_hash)s)
                ON CONFLICT (job_id) DO NOTHING
                """,
                job,
            )
            inserted += cur.rowcount

    print("Processed:", len(records))
    print("Inserted:", inserted)


if __name__ == "__main__":
    load_dotenv()

    greenhouse_raw = json.loads(Path("samples/greenhouse/axonius.json").read_text(encoding="utf-8"))["jobs"]
    comeet_raw = json.loads(Path("samples/comeet/kmslh.json").read_text(encoding="utf-8"))

    jobs = pd.concat([
        normalize_greenhouse(greenhouse_raw, "515673382"),
        normalize_comeet(comeet_raw, "512336231"),
    ], ignore_index=True)
    jobs = add_job_id_and_hash(jobs)

    save_jobs(jobs)

