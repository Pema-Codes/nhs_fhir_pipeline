import json
import os

import requests

# Set up project directory structure
DATA_DIR = os.path.join(".", "data", "raw_fhir")
os.makedirs(DATA_DIR, exist_ok=True)

# Public R4 HAPI FHIR Server Endpoint
BASE_URL = "http://hapi.fhir.org/baseR4"


def fetch_fhir_resource(resource_type: str, limit: int = 5):
    """Fetches a bundle of resources from the FHIR endpoint and saves the JSON."""
    url = f"{BASE_URL}/{resource_type}?_count={limit}&_format=json"
    headers = {"Accept": "application/fhir+json"}

    print(f"Fetching {limit} {resource_type} resources from {url}...")
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 200:
        bundle_data = response.json()
        file_path = os.path.join(DATA_DIR, f"raw_{resource_type.lower()}_bundle.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(bundle_data, f, indent=2)

        print(f"Successfully saved {resource_type} bundle to: {file_path}")
        return bundle_data
    else:
        print(f"Failed to fetch data. HTTP Status: {response.status_code}")
        return None


if __name__ == "__main__":
    # Fetch sample Patient and Observation bundles
    patients = fetch_fhir_resource("Patient", limit=10)
    observations = fetch_fhir_resource("Observation", limit=10)
