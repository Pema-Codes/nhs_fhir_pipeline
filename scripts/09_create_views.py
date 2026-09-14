import os
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nhs_fhir_staging.db")
VIEW_SQL_PATH = os.path.join(BASE_DIR, "sql", "02_fhir_analytics_views.sql")

engine = create_engine(f"sqlite:///{DB_PATH}")


def apply_views():
    print("Creating SQL analytics views...")
    with open(VIEW_SQL_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    with engine.connect() as conn:
        # Execute each statement separated by semicolon
        for statement in sql_script.split(";"):
            if statement.strip():
                conn.execute(text(statement))
        conn.commit()
    print("View 'vw_patient_clinical_timeline' successfully created!")


if __name__ == "__main__":
    apply_views()
