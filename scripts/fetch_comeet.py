import json
from pathlib import Path

import requests

url = "https://www.comeet.com/jobs/kmslh/97.008"

response = requests.get(url, timeout=30)
response.raise_for_status()

# the jobs are a JSON list inside the page, right after this variable name
page = response.text
start = page.index("[", page.index("COMPANY_POSITIONS_DATA ="))
positions, _ = json.JSONDecoder().raw_decode(page, start)

folder = Path("samples/comeet")
folder.mkdir(parents=True, exist_ok=True)

file = folder / "kmslh.json"
file.write_text(json.dumps(positions, ensure_ascii=False, indent=2), encoding="utf-8")

print("Jobs:", len(positions))
