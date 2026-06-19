import json
import os
from pathlib import Path
import requests

DOWNLOAD_DIR = Path("pdfs")
DOWNLOAD_DIR.mkdir(exist_ok=True)

with open("circular.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    url = item.get("link")

    if not url:
        continue

    filename = url.split("/")[-1]
    filepath = DOWNLOAD_DIR / filename

    # Skip already downloaded files
    if filepath.exists():
        print(f"Skipping {filename}")
        continue

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Downloaded: {filename}")

    except Exception as e:
        print(f"Failed {url}")
        print(e)
