import json
import os

# Define paths to sample files
patient_file = os.path.join("data", "raw_fhir", "patient_page_1.json")
observation_file = os.path.join("data", "raw_fhir", "observation_page_1.json")


def inspect_patients(file_path):
    print("--- PATIENT RESOURCE MAPPING ---")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    for entry in entries[:3]:  # Inspect first 3 records
        resource = entry.get("resource", {})

        patient_fhir_id = resource.get("id", "N/A")
        gender = resource.get("gender", "N/A")
        birth_date = resource.get("birthDate", "N/A")

        print(
            f"Patient ID: {patient_fhir_id} | Gender: {gender} | Birth Date: {birth_date}"
        )


def inspect_observations(file_path):
    print("\n--- OBSERVATION RESOURCE MAPPING ---")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    for entry in entries[:3]:  # Inspect first 3 records
        resource = entry.get("resource", {})

        obs_id = resource.get("id", "N/A")

        # Safely traverse code -> coding array -> first element -> code
        code_struct = resource.get("code", {})
        coding_list = code_struct.get("coding", [])
        loinc_code = coding_list[0].get("code", "N/A") if coding_list else "N/A"

        # Safely traverse valueQuantity
        value_quantity = resource.get("valueQuantity", {})
        result_value = value_quantity.get("value", "N/A")
        unit = value_quantity.get("unit", "N/A")

        print(
            f"Obs ID: {obs_id} | LOINC: {loinc_code} | Value: {result_value} | Unit: {unit}"
        )


if __name__ == "__main__":
    inspect_patients(patient_file)
    inspect_observations(observation_file)
