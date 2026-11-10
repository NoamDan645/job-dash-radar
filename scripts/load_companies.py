import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

folder = Path("../techmap/companies")

comeet_count = 0
greenhouse_count = 0

with psycopg.connect(
    host="localhost",
    port=5432,
    user="noam",
    password=os.environ["POSTGRES_PASSWORD"],
    dbname="jobradar",
) as conn:
    for file in folder.glob("*.json"):
        company = json.loads(file.read_text(encoding="utf-8"))
        company_id = file.stem

        if company.get("comeetId"):
            ats_type = "comeet"
            ats_id = company["comeetId"]
            comeet_count += 1
        elif company.get("greenhouseId"):
            ats_type = "greenhouse"
            ats_id = company["greenhouseId"]
            greenhouse_count += 1
        else:
            continue

        conn.execute(
            """
            INSERT INTO companies (company_id, name, ats_type, ats_id, careers_url, city, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (company_id) DO UPDATE SET
                name = EXCLUDED.name,
                ats_type = EXCLUDED.ats_type,
                ats_id = EXCLUDED.ats_id,
                careers_url = EXCLUDED.careers_url,
                city = EXCLUDED.city,
                is_active = EXCLUDED.is_active
            """,
            (company_id, company["name"], ats_type, ats_id,
             company["careersUrl"], company["addresses"][0]["city"], company["isActive"]),
        )

print("Comeet:", comeet_count)
print("Greenhouse:", greenhouse_count)
print("Total:", comeet_count + greenhouse_count)