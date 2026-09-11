import json
import os

# Path to the project file
patient_file = os.path.join("data", "raw_fhir", "patient_page_1.json")

# Open and load the FHIR bundle
with open(patient_file, "r", encoding="utf-8") as f:
    bundle = json.load(f)

# Extract the "entry" list safely
entries = bundle.get("entry", [])
print(f"Total patient entries found: {len(entries)}")
