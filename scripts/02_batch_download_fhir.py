import json
import os
import time
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw_fhir")
os.makedirs(DATA_DIR, exist_ok=True)

BASE_URL = "http://hapi.fhir.org/baseR4"


def batch_fetch_resources(
    resource_type: str, total_records: int = 50, page_size: int = 10
):
    collected = 0
    page = 1
    next_url = f"{BASE_URL}/{resource_type}?_count={page_size}&_format=json"

    print(f"\n--- Batch Fetching {resource_type} Records ---")

    while next_url and collected < total_records:
        try:
            print(f"Fetching Page {page}...")
            response = requests.get(
                next_url, headers={"Accept": "application/fhir+json"}, timeout=15
            )

            if response.status_code != 200:
                print(f"Failed page {page}. Status: {response.status_code}")
                break

            data = response.json()
            entries = data.get("entry", [])

            if not entries:
                break

            file_name = f"{resource_type.lower()}_page_{page}.json"
            file_path = os.path.join(DATA_DIR, file_name)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            collected += len(entries)
            print(f"Saved {file_name} ({collected}/{total_records} total)")

            # Get next page link from FHIR header
            links = data.get("link", [])
            next_url = None
            for link in links:
                if link.get("relation") == "next":
                    next_url = link.get("url")
                    break

            page += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"Done downloading {collected} {resource_type} records!\n")


if __name__ == "__main__":
    batch_fetch_resources("Patient", total_records=50, page_size=10)
    batch_fetch_resources("Observation", total_records=50, page_size=10)
