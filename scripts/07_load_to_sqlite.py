import os
import pandas as pd
from sqlalchemy import create_engine, text

print("Starting SQLAlchemy ingestion pipeline...")

# 1. Define File Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nhs_fhir_staging.db")
PATIENTS_CSV = os.path.join(BASE_DIR, "data", "patients_clean.csv")
OBSERVATIONS_CSV = os.path.join(BASE_DIR, "data", "observations_clean.csv")
SCHEMA_SQL = os.path.join(BASE_DIR, "sql", "01_schema_ddl.sql")

# 2. Create SQLAlchemy Engine
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def initialize_database():
    """Drops existing tables and initializes a clean DDL schema."""
    print("Resetting and initializing database schema...")

    # Drop existing tables to avoid duplicate constraint errors
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF;"))
        conn.execute(text("DROP TABLE IF EXISTS fhir_observations;"))
        conn.execute(text("DROP TABLE IF EXISTS terminology_lookup;"))
        conn.execute(text("DROP TABLE IF EXISTS fhir_patients;"))
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        conn.commit()

    # Read and apply DDL statements
    with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
        schema_script = f.read()

    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        for statement in schema_script.split(";"):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()
    print("Database schema initialized successfully.")


def load_data():
    """Loads clean CSVs into pandas DataFrames and ingests into SQLite via SQLAlchemy."""
    print("Reading clean staging files...")
    df_patients = pd.read_csv(PATIENTS_CSV)
    df_observations = pd.read_csv(OBSERVATIONS_CSV)

    # Deduplicate patients and observations
    df_patients = df_patients.drop_duplicates(subset=["patient_fhir_id"])
    df_observations = df_observations.drop_duplicates(subset=["obs_id"])

    # Clean patient_fhir_id references
    if "patient_reference" in df_observations.columns:
        df_observations["patient_fhir_id"] = (
            df_observations["patient_reference"]
            .astype(str)
            .str.replace("Patient/", "", regex=False)
            .str.replace("urn:uuid:", "", regex=False)
        )
    elif "patient_fhir_id" in df_observations.columns:
        df_observations["patient_fhir_id"] = (
            df_observations["patient_fhir_id"]
            .astype(str)
            .str.replace("Patient/", "", regex=False)
            .str.replace("urn:uuid:", "", regex=False)
        )

    # Extract distinct LOINC terms
    df_terminology = (
        df_observations[["loinc_code", "display_name"]]
        .drop_duplicates(subset=["loinc_code"])
        .fillna({"display_name": "Unknown Display Name"})
    )

    print("Ingesting data via SQLAlchemy...")

    with engine.connect() as conn:
        # 1. Ingest Patients
        df_patients.to_sql("fhir_patients", con=conn, if_exists="append", index=False)
        print(f"  └─ Ingested {len(df_patients)} patients into 'fhir_patients'")

        # 2. Ingest Terminology
        df_terminology.to_sql(
            "terminology_lookup", con=conn, if_exists="append", index=False
        )
        print(f"  └─ Ingested {len(df_terminology)} terms into 'terminology_lookup'")

        # 3. Filter Observations for Foreign Key Integrity
        valid_cols = [
            "obs_id",
            "patient_fhir_id",
            "loinc_code",
            "result_value",
            "unit",
            "effective_datetime",
        ]
        df_obs_clean = df_observations[
            [c for c in valid_cols if c in df_observations.columns]
        ]

        # Keep only observations referencing valid patients and LOINC codes
        valid_patients = set(df_patients["patient_fhir_id"])
        valid_terms = set(df_terminology["loinc_code"])

        df_obs_clean = df_obs_clean[
            df_obs_clean["patient_fhir_id"].isin(valid_patients)
            & df_obs_clean["loinc_code"].isin(valid_terms)
        ]

        # 4. Ingest Validated Observations
        df_obs_clean.to_sql(
            "fhir_observations", con=conn, if_exists="append", index=False
        )
        print(
            f"  └─ Ingested {len(df_obs_clean)} validated observations into 'fhir_observations'"
        )

        conn.commit()

    print("Ingestion pipeline complete!")
