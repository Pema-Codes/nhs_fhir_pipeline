import json
import os
import glob
import pandas as pd

# Define directory paths
RAW_DIR = os.path.join("data", "raw_fhir")
OUTPUT_CSV = os.path.join("data", "observations_clean.csv")


def extract_observation_data(resource):
    """
    Safely extracts key clinical attributes from a FHIR Observation resource.
    Focuses on LOINC codes, clinical values, units, timestamps, and patient links.
    """
    obs_id = resource.get("id", "N/A")

    # Safely extract linked Patient reference ID (e.g., "Patient/sindhu-syn-000005")
    subject = resource.get("subject", {})
    patient_ref = subject.get("reference", "N/A")

    # Safely traverse code -> coding array -> first element -> code/display
    code_struct = resource.get("code", {})
    coding_list = code_struct.get("coding", [])

    loinc_code = "N/A"
    display_name = "N/A"
    if coding_list and isinstance(coding_list, list):
        loinc_code = coding_list[0].get("code", "N/A")
        display_name = coding_list[0].get("display", "N/A")

    # Safely extract quantitative value and unit
    value_quantity = resource.get("valueQuantity", {})
    result_value = value_quantity.get("value", "N/A")
    unit = value_quantity.get("unit", "N/A")

    # Extract observation timestamp (effectiveDateTime or issued)
    effective_dt = resource.get("effectiveDateTime", resource.get("issued", "N/A"))

    return {
        "obs_id": obs_id,
        "patient_reference": patient_ref,
        "loinc_code": loinc_code,
        "display_name": display_name,
        "result_value": result_value,
        "unit": unit,
        "effective_datetime": effective_dt,
    }


def process_all_observation_bundles():
    """
    Iterates through all raw Observation JSON files in the data lake,
    parses entries, and exports a unified Pandas DataFrame / CSV.
    """
    obs_files = glob.glob(os.path.join(RAW_DIR, "observation_page_*.json"))

    if not obs_files:
        print(f"No observation JSON files found in {RAW_DIR}")
        return

    extracted_records = []

    for file_path in obs_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                bundle = json.load(f)
                entries = bundle.get("entry", [])

                for entry in entries:
                    resource = entry.get("resource", {})
                    # Ensure we are strictly processing Observation resource types
                    if resource.get("resourceType") == "Observation":
                        record = extract_observation_data(resource)
                        extracted_records.append(record)

            except json.JSONDecodeError:
                print(f"Skipping malformed JSON file: {file_path}")

    # Convert to Pandas DataFrame
    df = pd.DataFrame(extracted_records)

    # Display summary to terminal
    print("--- OBSERVATION & LOINC PARSING COMPLETE ---")
    print(f"Total Observation Records Processed: {len(df)}")
    print("\nFirst 5 Processed Records:")
    print(df.head())

    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nClean dataset saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    process_all_observation_bundles()
