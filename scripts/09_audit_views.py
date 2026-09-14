import os
import pandas as pd
from sqlalchemy import create_engine

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nhs_fhir_staging.db")

engine = create_engine(f"sqlite:///{DB_PATH}")


def audit_clinical_views():
    print("Auditing 'vw_patient_clinical_timeline'...\n")

    # 1. Load full view into pandas
    query = "SELECT * FROM vw_patient_clinical_timeline;"
    df = pd.read_sql(query, con=engine)

    # 2. Display Flag Summary
    print("Clinical Flag Breakdown:")
    print(df["clinical_flag"].value_counts().to_string())
    print("-" * 50)

    # 3. Inspect Flagged Observations
    flagged_df = df[df["clinical_flag"] != "Normal / Unflagged"]
    if not flagged_df.empty:
        print(f"⚠️ Found {len(flagged_df)} Flagged Clinical Observations:\n")
        print(
            flagged_df[
                [
                    "patient_fhir_id",
                    "test_name",
                    "result_value",
                    "unit",
                    "clinical_flag",
                ]
            ]
            .head(10)
            .to_string(index=False)
        )
    else:
        print("No abnormal flags triggered across staged observations.")


if __name__ == "__main__":
    audit_clinical_views()
