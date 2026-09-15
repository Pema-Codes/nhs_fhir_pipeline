import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(
    page_title="NHS Clinical Analytics Dashboard", page_icon="🏥", layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "nhs_fhir_staging.db")
engine = create_engine(f"sqlite:///{DB_PATH}")


@st.cache_data(ttl=60)
def load_timeline_data():
    """Fetches records from the vw_patient_clinical_timeline view."""
    query = "SELECT * FROM vw_patient_clinical_timeline;"
    df = pd.read_sql(query, con=engine)

    # Standardize timezones by setting utc=True
    df["birth_date"] = pd.to_datetime(df["birth_date"], errors="coerce")
    df["effective_datetime"] = pd.to_datetime(
        df["effective_datetime"], utc=True, errors="coerce"
    )
    df["result_value"] = pd.to_numeric(df["result_value"], errors="coerce")

    return df


st.title("🏥 NHS FHIR Clinical Analytics Dashboard")
st.markdown("Interoperability Staging Layer — Data Visualizations & Risk Monitoring")

df = load_timeline_data()

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Patients", df["patient_fhir_id"].nunique())
m2.metric("Total Observations", len(df))
flagged = len(df[df["clinical_flag"] != "Normal / Unflagged"])
m3.metric("Flagged Observations", flagged)
m4.metric("LOINC Tests Mapped", df["test_name"].nunique())

st.divider()
st.subheader("📋 Patient Clinical Timeline")
st.dataframe(df, use_container_width=True)

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 Clinical Flag Distribution")
    st.bar_chart(df["clinical_flag"].value_counts())
with c2:
    st.subheader("🧪 Observations per Test")
    st.bar_chart(df["test_name"].value_counts())
