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
    CASE 
        -- Systolic Blood Pressure
        WHEN (o.loinc_code LIKE '%8480-6%' OR LOWER(t.display_name) LIKE '%systolic%') 
             AND CAST(o.result_value AS REAL) > 140.0 THEN 'High Blood Pressure'
        WHEN (o.loinc_code LIKE '%8480-6%' OR LOWER(t.display_name) LIKE '%systolic%') 
             AND CAST(o.result_value AS REAL) < 90.0 THEN 'Low Blood Pressure'
        
        -- Diastolic Blood Pressure
        WHEN (o.loinc_code LIKE '%8462-4%' OR LOWER(t.display_name) LIKE '%diastolic%') 
             AND CAST(o.result_value AS REAL) > 90.0 THEN 'High Blood Pressure'
        
        -- Body Mass Index (BMI)
        WHEN (o.loinc_code LIKE '%39156-5%' OR LOWER(t.display_name) LIKE '%body mass index%') 
             AND CAST(o.result_value AS REAL) >= 30.0 THEN 'Obese'
        WHEN (o.loinc_code LIKE '%39156-5%' OR LOWER(t.display_name) LIKE '%body mass index%') 
             AND CAST(o.result_value AS REAL) >= 25.0 THEN 'Overweight'
        
        -- Heart Rate
        WHEN (o.loinc_code LIKE '%8867-4%' OR LOWER(t.display_name) LIKE '%heart rate%') 
             AND CAST(o.result_value AS REAL) > 100.0 THEN 'Tachycardia'
        WHEN (o.loinc_code LIKE '%8867-4%' OR LOWER(t.display_name) LIKE '%heart rate%') 
             AND CAST(o.result_value AS REAL) < 60.0 THEN 'Bradycardia'

        -- Body Temperature (LOINC: 8310-5)
        WHEN (o.loinc_code LIKE '%8310-5%' OR LOWER(t.display_name) LIKE '%body temperature%') 
             AND CAST(o.result_value AS REAL) > 38.0 THEN 'Fever'
        
        ELSE 'Normal / Unflagged'
    END AS clinical_flag
FROM fhir_patients p
INNER JOIN fhir_observations o ON p.patient_fhir_id = o.patient_fhir_id
LEFT JOIN terminology_lookup t ON o.loinc_code = t.loinc_code
ORDER BY o.effective_datetime DESC;