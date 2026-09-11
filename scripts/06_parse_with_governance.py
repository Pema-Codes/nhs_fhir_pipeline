import json
import os
import glob
import logging
import pandas as pd

# 1. Setup Information Governance Error Logging
LOG_FILE = os.path.join("logs", "fhir_ingestion_errors.log")
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

RAW_DIR = os.path.join("data", "raw_fhir")
PATIENTS_CSV = os.path.join("data", "patients_clean.csv")
OBSERVATIONS_CSV = os.path.join("data", "observations_clean.csv")


def validate_and_parse_patient(resource, file_name):
    """Validates patient resource for mandatory IG fields."""
    patient_id = resource.get("id")

    # IG Rule: Patient record MUST have a valid ID
    if not patient_id:
        logging.warning(
            f"IG VALIDATION FAILURE [Patient]: Missing mandatory 'id' in file {file_name}"
        )
        return None

    address_list = resource.get("address", [])
    postal_code = (
        address_list[0].get("postalCode", "N/A")
        if address_list and isinstance(address_list, list)
        else "N/A"
    )

    return {
        "patient_fhir_id": patient_id,
        "gender": resource.get("gender", "N/A"),
        "birth_date": resource.get("birthDate", "N/A"),
        "postal_code": postal_code,
    }


def validate_and_parse_observation(resource, file_name):
    """Validates observation resource for mandatory IG fields."""
    obs_id = resource.get("id")
    subject_ref = resource.get("subject", {}).get("reference")

    # IG Rule: Observation MUST have both an ID and a valid Patient Subject Reference
    if not obs_id:
        logging.warning(
            f"IG VALIDATION FAILURE [Observation]: Missing mandatory 'id' in file {file_name}"
        )
        return None
    if not subject_ref:
        logging.warning(
            f"IG VALIDATION FAILURE [Observation]: Missing mandatory 'subject.reference' for Observation ID '{obs_id}' in file {file_name}"
        )
        return None

    code_struct = resource.get("code", {})
    coding_list = code_struct.get("coding", [])
    loinc_code = coding_list[0].get("code", "N/A") if coding_list else "N/A"
    display_name = coding_list[0].get("display", "N/A") if coding_list else "N/A"

    value_quantity = resource.get("valueQuantity", {})

    return {
        "obs_id": obs_id,
        "patient_reference": subject_ref,
        "loinc_code": loinc_code,
        "display_name": display_name,
        "result_value": value_quantity.get("value", "N/A"),
        "unit": value_quantity.get("unit", "N/A"),
        "effective_datetime": resource.get(
            "effectiveDateTime", resource.get("issued", "N/A")
        ),
    }


def run_governance_pipeline():
    patient_records, observation_records = [], []
    json_files = glob.glob(os.path.join(RAW_DIR, "*.json"))

    for file_path in json_files:
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                bundle = json.load(f)
                entries = bundle.get("entry", [])

                for entry in entries:
                    resource = entry.get("resource", {})
                    res_type = resource.get("resourceType")

                    if res_type == "Patient":
                        record = validate_and_parse_patient(resource, file_name)
                        if record:
                            patient_records.append(record)
                    elif res_type == "Observation":
                        record = validate_and_parse_observation(resource, file_name)
                        if record:
                            observation_records.append(record)

            except json.JSONDecodeError:
                logging.error(
                    f"CORRUPT FILE: Malformed JSON structure in file {file_name}"
                )

    # Export Validated DataFrames
    df_patients = pd.DataFrame(patient_records)
    df_observations = pd.DataFrame(observation_records)

    df_patients.to_csv(PATIENTS_CSV, index=False)
    df_observations.to_csv(OBSERVATIONS_CSV, index=False)

    print("--- GOVERNANCE ETL PIPELINE EXECUTED ---")
    print(f"Valid Patients Exported: {len(df_patients)}")
    print(f"Valid Observations Exported: {len(df_observations)}")
    print(f"Error Log Updated: {LOG_FILE}")


if __name__ == "__main__":
    run_governance_pipeline()
