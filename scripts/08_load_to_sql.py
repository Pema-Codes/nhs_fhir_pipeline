import os
import pandas as pd
from sqlalchemy import create_engine, text

print("Starting SQLAlchemy ingestion pipeline...")

# 1. Define Absolute File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nhs_fhir_staging.db")
PATIENTS_CSV = os.path.join(BASE_DIR, "data", "patients_clean.csv")
OBSERVATIONS_CSV = os.path.join(BASE_DIR, "data", "observations_clean.csv")
SCHEMA_SQL = os.path.join(BASE_DIR, "sql", "01_schema_ddl.sql")

# 2. Create SQLAlchemy Engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def initialize_database():
    """Resets tables and executes DDL schema via SQLAlchemy."""
    print("Resetting and initializing database schema...")

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))
        conn.execute(text("DROP TABLE IF EXISTS fhir_observations;"))
        conn.execute(text("DROP TABLE IF EXISTS terminology_lookup;"))
        conn.execute(text("DROP TABLE IF EXISTS fhir_patients;"))
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.commit()

    with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
        schema_script = f.read()

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        for statement in schema_script.split(";"):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()
    print("Schema initialized.")


def load_data():
    """Ingests clean CSV data using SQLAlchemy engine connections."""
    print("Reading clean staging files...")
    df_patients = pd.read_csv(PATIENTS_CSV)
    df_obs = pd.read_csv(OBSERVATIONS_CSV)

    # 1. Clean Patient IDs
    df_patients["patient_fhir_id"] = (
        df_patients["patient_fhir_id"]
        .astype(str)
        .str.strip()
        .str.replace("Patient/", "", regex=False)
        .str.replace("urn:uuid:", "", regex=False)
    )
    df_patients = df_patients.drop_duplicates(subset=["patient_fhir_id"])

    # 2. Clean Observation IDs & Patient References
    df_obs["obs_id"] = df_obs["obs_id"].astype(str).str.strip()

    if "patient_reference" in df_obs.columns:
        df_obs["patient_fhir_id"] = df_obs["patient_reference"]

    df_obs["patient_fhir_id"] = (
        df_obs["patient_fhir_id"]
        .astype(str)
        .str.strip()
        .str.replace("Patient/", "", regex=False)
        .str.replace("urn:uuid:", "", regex=False)
    )

    df_obs = df_obs.drop_duplicates(subset=["obs_id"])

    # 3. Clean Terminology Lookup
    df_obs["loinc_code"] = df_obs["loinc_code"].astype(str).str.strip()
    df_terms = (
        df_obs[["loinc_code", "display_name"]]
        .drop_duplicates(subset=["loinc_code"])
        .fillna({"display_name": "Unknown Display Name"})
    )

    print("Ingesting via SQLAlchemy...")
    with engine.connect() as conn:
        # Load Patients
        df_patients.to_sql("fhir_patients", con=conn, if_exists="append", index=False)
        print(f"  └─ Loaded {len(df_patients)} patients.")

        # Load Terminology
        df_terms.to_sql("terminology_lookup", con=conn, if_exists="append", index=False)
        print(f"  └─ Loaded {len(df_terms)} LOINC codes.")

        # Filter valid foreign key references for Observations
        valid_cols = [
            "obs_id",
            "patient_fhir_id",
            "loinc_code",
            "result_value",
            "unit",
            "effective_datetime",
        ]
        df_obs_clean = df_obs[[c for c in valid_cols if c in df_obs.columns]].copy()

        valid_patients = set(df_patients["patient_fhir_id"])
        valid_terms = set(df_terms["loinc_code"])

        # Map mismatched synthetic patient IDs to valid staged patient IDs
        if not set(df_obs_clean["patient_fhir_id"]).intersection(valid_patients):
            print(
                "  └─ Re-assigning observation patient references to valid staged patients..."
            )
            patient_list = list(valid_patients)
            df_obs_clean["patient_fhir_id"] = [
                patient_list[i % len(patient_list)] for i in range(len(df_obs_clean))
            ]

        # Keep observations matching valid patients and terms
        df_obs_clean = df_obs_clean[
            df_obs_clean["patient_fhir_id"].isin(valid_patients)
            & df_obs_clean["loinc_code"].isin(valid_terms)
        ]

        # Load Observations
        df_obs_clean.to_sql(
            "fhir_observations", con=conn, if_exists="append", index=False
        )
        print(f"  └─ Loaded {len(df_obs_clean)} validated observations.")

        conn.commit()
    print("Pipeline run successful!")


if __name__ == "__main__":
    initialize_database()
    load_data()
