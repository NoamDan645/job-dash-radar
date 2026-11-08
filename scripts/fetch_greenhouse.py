from pathlib import Path

import requests

url = "https://boards-api.greenhouse.io/v1/boards/axonius/jobs?content=true"

response = requests.get(url, timeout=30)
response.raise_for_status()

folder = Path("samples/greenhouse")
folder.mkdir(parents=True, exist_ok=True)

file = folder / "axonius.json"
file.write_text(response.text, encoding="utf-8")

print("Jobs:", len(response.json()["jobs"]))