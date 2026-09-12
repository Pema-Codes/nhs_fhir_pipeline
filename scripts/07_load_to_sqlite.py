import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join("data", "nhs_fhir_staging.db")
DDL_PATH = os.path.join("sql", "01_schema_ddl.sql")
PATIENTS_CSV = os.path.join("data", "patients_clean.csv")
OBSERVATIONS_CSV = os.path.join("data", "observations_clean.csv")


def build_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Execute DDL Schema
    with open(DDL_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
    print("✓ Schema DDL executed successfully.")

    # 2. Populate Patients Table
    df_patients = pd.DataFrame()
    if os.path.exists(PATIENTS_CSV):
        df_patients = pd.read_csv(PATIENTS_CSV).drop_duplicates(
            subset=["patient_fhir_id"]
        )
        df_patients.to_sql("fhir_patients", conn, if_exists="append", index=False)
        print(f"✓ Loaded {len(df_patients)} unique patients into 'fhir_patients'.")

    # 3. Populate Terminology Lookup & Observations Tables
    if os.path.exists(OBSERVATIONS_CSV):
        df_obs = pd.read_csv(OBSERVATIONS_CSV)

        # Clean subject reference across all common FHIR formats
        if "patient_reference" in df_obs.columns:
            df_obs["patient_fhir_id"] = (
                df_obs["patient_reference"]
                .astype(str)
                .str.replace("Patient/", "", regex=False)
                .str.replace("urn:uuid:", "", regex=False)
            )

        # Build Terminology Lookup Table safely
        if "loinc_code" in df_obs.columns:
            df_terms = df_obs[["loinc_code", "display_name", "unit"]].copy()
            df_terms.rename(columns={"unit": "target_unit"}, inplace=True)
            df_terms["display_name"] = df_terms["display_name"].fillna(
                "Unknown Display Name"
            )
            df_terms = df_terms.dropna(subset=["loinc_code"]).drop_duplicates(
                subset=["loinc_code"]
            )
            df_terms.to_sql("terminology_lookup", conn, if_exists="append", index=False)
            print(f"✓ Loaded {len(df_terms)} LOINC codes into 'terminology_lookup'.")

        # Clean observation columns matching DDL schema
        valid_cols = [
            "obs_id",
            "patient_fhir_id",
            "loinc_code",
            "result_value",
            "unit",
            "effective_datetime",
        ]
        df_obs_clean = df_obs[
            [c for c in valid_cols if c in df_obs.columns]
        ].drop_duplicates(subset=["obs_id"])

        # Load observations directly to avoid dropping valid rows
        df_obs_clean.to_sql("fhir_observations", conn, if_exists="append", index=False)
        print(f"✓ Loaded {len(df_obs_clean)} observations into 'fhir_observations'.")

    conn.close()
    print(f"\n--- SUCCESS: Database built at {DB_PATH} ---")


if __name__ == "__main__":
    build_database()
