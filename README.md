# HL7 FHIR Interoperability & Data Pipeline

A local data engineering pipeline designed to extract, batch-process, and stage standardized healthcare records from a public HL7 FHIR (R4) REST API. Built to demonstrate clinical data ingestion, API pagination, and Data Lake staging patterns.

---

## Tech Stack & Healthcare Standards

* **Clinical Standards:** HL7 FHIR (R4), LOINC Terminology, SNOMED CT
* **Languages & Libraries:** Python 3, requests, json, os, time
* **Tools & Environment:** Git, GitHub, VS Code

---

## Repository Structure

```text
nhs_fhir_pipeline/
├── data/
│   └── raw_fhir/                # Raw Staging Layer / Data Lake
│       ├── patient_page_1.json ... patient_page_5.json
│       └── observation_page_1.json ... observation_page_5.json
├── scripts/
│   ├── 01_fetch_fhir.py         # Single-resource API extractor
│   └── 02_batch_download_fhir.py# Automated link-header pagination pipeline
└── README.md
```
## Key Pipeline Features

**Standardized Ingestion:** Programmatically queries FHIR REST API endpoints with explicit Accept: application/fhir+json headers to retrieve valid JSON resources (Patient, Observation).

**Automated Batch Pagination:** Dynamically traverses FHIR bundle response metadata (link array where "relation": "next") to sequentially harvest multi-page datasets without missing records.

**Data Lake Staging Layer:** Stores unparsed raw JSON payloads in data/raw_fhir/ to maintain an immutable audit trail and prevent redundant API load during development.

**Resilient API Handling:** Built with robust defensive code, using non-crashing .get() lookup logic, network error handling (try/except), and rate-limiting delays (time.sleep) for API etiquette.

---

##  Development Progress Logs
<details>
<summary><b>Day 1: Project Setup & Single-Resource Ingestion</b></summary>

* **Objective:** Establish environment and construct a foundational single-resource FHIR API extractor.
* **Key Achievements:**
  * Initialized local project directory and configured version control.
  * Created `01_fetch_fhir.py` using `requests` with strict `Accept: application/fhir+json` headers.
  * Extracted initial `Patient` and `Observation` JSON bundles into raw staging (`data/raw_fhir/`).
  * Implemented safe dictionary retrieval (`.get()`) to gracefully handle optional clinical fields without script failure.

</details>

<details>
<summary><b>Day 2: Dynamic API Pagination & Data Lake Staging</b></summary>

* **Objective:** Automate batch extraction across multi-page FHIR response bundles.
* **Key Achievements:**
  * Refactored extractor in `02_batch_download_fhir.py` using a dynamic `while` loop.
  * Embedded link-header detection (`"relation": "next"`) to sequentially request consecutive record pages.
  * Ingested 50 `Patient` and 50 `Observation` records across 10 staged JSON files.
  * Added `time.sleep(0.5)` rate-limiting to adhere to public API usage guidelines.
  * Fixed directory path structure and committed stable data lake assets to GitHub.

</details>

<details>
<summary><b>Day 3: FHIR Schema Inspection & Relational Mapping</b></summary>

* **Objective:** Inspect nested FHIR JSON resources (`Patient` and `Observation`) and map specific keys to relational database column equivalents.
* **Key Achievements:**
  * Developed `scripts/03_inspect_fhir.py` to parse raw JSON bundles stored in the Data Lake (`data/raw_fhir/`).
  * Mapped Patient demographics: `id` → `patient_fhir_id`, `gender` → `gender`, and `birthDate` → `birth_date`.
  * Navigated complex nested objects in Observations: extracted LOINC codes from `code.coding[0].code` and clinical measurements from `valueQuantity`.
  * Implemented defensive list and dictionary lookups to handle missing optional fields cleanly.

</details>

<details>
<summary><b>Day 4: Staging Patient Demographics Parser</b></summary>

* **Objective:** Build a dedicated ETL script to parse raw Patient JSON bundles into flat tabular structures.
* **Key Achievements:**
  * Developed `scripts/04_parse_patients.py` to extract 50 patient demographic records into `data/patients_clean.csv`.
  * Navigated nested FHIR JSON fields including `id`, `gender`, `birthDate`, and `address[0].postalCode`.
  * Implemented defensive `.get()` lookups to handle missing optional fields safely and avoid execution errors.

</details>

<details>
<summary><b>Day 5: Clinical Telemetry & LOINC Observation Parser</b></summary>

* **Objective:** Parse raw FHIR Observation JSON resources to extract clinical measurements, standardized LOINC codes, values, units, and timestamps.
* **Key Achievements:**
  * Created `scripts/05_parse_observations.py` to batch-process clinical telemetry into `data/observations_clean.csv`.
  * Extracted LOINC codes (`code.coding[0].code`) and clinical measurement values/units (`valueQuantity`).
  * Linked clinical observations to patient entities via `subject.reference` foreign keys.
  * Preserved temporal metadata (`effectiveDateTime`) to support time-series clinical reporting.

</details>

<details>
<summary><b>Day 6: Information Governance & Automated Error Logging</b></summary>

* **Objective:** Implement data validation rules to log malformed FHIR records and enforce Information Governance (IG) standards.
* **Key Achievements:**
  * Created `scripts/06_parse_with_governance.py` featuring automated exception handling and logging.
  * Configured Python `logging` module to capture validation failures (missing `id` or unlinked `subject.reference`) into `logs/fhir_ingestion_errors.log`.
  * Ensured pipeline resilience by skipping invalid records without halting batch processing execution.
  * Verified local clean CSV exports for clinical auditing.

</details>

##  Quick Start

    Clone the repository:

    git clone [https://github.com/Pema-Codes/nhs_fhir_pipeline.git](https://github.com/Pema-Codes/nhs_fhir_pipeline.git)
    cd nhs_fhir_pipeline

    Run single-resource extractor:
    
    python scripts/01_fetch_fhir.py

    Run automated batch pagination pipeline:

    python scripts/02_batch_download_fhir.py
