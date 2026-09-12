-- NHS FHIR Interoperability Pipeline: Relational Staging Schema
-- Engine: SQLite / PostgreSQL compliant DDL

-- 1. Patients Master Table
CREATE TABLE IF NOT EXISTS fhir_patients (
    patient_fhir_id TEXT PRIMARY KEY,
    gender TEXT,
    birth_date TEXT,
    postal_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Terminology Lookup Table (LOINC Metadata)
CREATE TABLE IF NOT EXISTS terminology_lookup (
    loinc_code TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    target_unit TEXT
);

-- 3. Observations Fact Table (Linked to Patients and Terminology)
CREATE TABLE IF NOT EXISTS fhir_observations (
    obs_id TEXT PRIMARY KEY,
    patient_fhir_id TEXT NOT NULL,
    loinc_code TEXT,
    result_value REAL,
    unit TEXT,
    effective_datetime TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_fhir_id) REFERENCES fhir_patients (patient_fhir_id) ON DELETE CASCADE,
    FOREIGN KEY (loinc_code) REFERENCES terminology_lookup (loinc_code)
);

-- Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_obs_patient ON fhir_observations (patient_fhir_id);
CREATE INDEX IF NOT EXISTS idx_obs_loinc ON fhir_observations (loinc_code);
