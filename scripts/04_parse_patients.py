pip install pandas

import json
import os
import glob
import pandas as pd

# Define paths
RAW_DIR = os.path.join("data", "raw_fhir")
OUTPUT_CSV = os.path.join("data", "patients_clean.csv")


def extract_patient_data(resource):
    """
    Safely extracts target demographic fields from a single FHIR Patient resource.
    Uses defensive .get() calls to handle optional/missing fields.
    """
    patient_id = resource.get("id", "N/A")
    gender = resource.get("gender", "N/A")
    birth_date = resource.get("birthDate", "N/A")

    # Extract postal code safely from nested address array
    address_list = resource.get("address", [])
    postal_code = "N/A"
    if address_list and isinstance(address_list, list):
        # Retrieve postalCode from the first address entry if present
        postal_code = address_list[0].get("postalCode", "N/A")

    return {
        "patient_fhir_id": patient_id,
        "gender": gender,
        "birth_date": birth_date,
        "postal_code": postal_code,
    }


def process_all_patient_bundles():
    """
    Iterates through all raw Patient JSON files in the data lake,
    parses entries, and exports a unified Pandas DataFrame / CSV.
    """
    patient_files = glob.glob(os.path.join(RAW_DIR, "patient_page_*.json"))

    if not patient_files:
        print(f"No patient JSON files found in {RAW_DIR}")
        return

    extracted_records = []

    for file_path in patient_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                bundle = json.load(f)
                entries = bundle.get("entry", [])

                for entry in entries:
                    resource = entry.get("resource", {})
                    # Ensure we are strictly processing Patient resource types
                    if resource.get("resourceType") == "Patient":
                        record = extract_patient_data(resource)
                        extracted_records.append(record)

            except json.JSONDecodeError:
                print(f"Skipping malformed JSON file: {file_path}")

    # Convert to Pandas DataFrame
    df = pd.DataFrame(extracted_records)

    # Display summary to terminal
    print("--- PATIENT PARSING COMPLETE ---")
    print(f"Total Patient Records Processed: {len(df)}")
    print("\nFirst 5 Processed Records:")
    print(df.head())

    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nClean dataset saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    process_all_patient_bundles()
