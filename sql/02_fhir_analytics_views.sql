-- sql/02_fhir_analytics_views.sql
-- Day 9: Create patient clinical timeline view with automated physiological flags

DROP VIEW IF EXISTS vw_patient_clinical_timeline;

CREATE VIEW vw_patient_clinical_timeline AS
SELECT 
    p.patient_fhir_id,
    p.gender,
    p.birth_date,
    o.obs_id,
    o.loinc_code,
    COALESCE(t.display_name, 'Unknown Test') AS test_name,
    o.result_value,
    o.unit,
    o.effective_datetime,
    -- Physiological risk flagging using standard clinical thresholds
    CASE 
        -- Systolic Blood Pressure (LOINC: 8480-6 or similar SBP tests)
        WHEN o.loinc_code = '8480-6' AND CAST(o.result_value AS REAL) > 140.0 THEN 'High Blood Pressure'
        WHEN o.loinc_code = '8480-6' AND CAST(o.result_value AS REAL) < 90.0 THEN 'Low Blood Pressure'
        
        -- Diastolic Blood Pressure (LOINC: 8462-4)
        WHEN o.loinc_code = '8462-4' AND CAST(o.result_value AS REAL) > 90.0 THEN 'High Blood Pressure'
        
        -- Body Mass Index (LOINC: 39156-5)
        WHEN o.loinc_code = '39156-5' AND CAST(o.result_value AS REAL) >= 30.0 THEN 'Obese'
        WHEN o.loinc_code = '39156-5' AND CAST(o.result_value AS REAL) >= 25.0 THEN 'Overweight'
        
        -- Heart Rate (LOINC: 8867-4)
        WHEN o.loinc_code = '8867-4' AND CAST(o.result_value AS REAL) > 100.0 THEN 'Tachycardia'
        WHEN o.loinc_code = '8867-4' AND CAST(o.result_value AS REAL) < 60.0 THEN 'Bradycardia'
        
        ELSE 'Normal / Unflagged'
    END AS clinical_flag
FROM fhir_patients p
INNER JOIN fhir_observations o 
    ON p.patient_fhir_id = o.patient_fhir_id
LEFT JOIN terminology_lookup t 
    ON o.loinc_code = t.loinc_code
ORDER BY o.effective_datetime DESC;