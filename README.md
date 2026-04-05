# FHIR Data Parser & Clinical Analytics

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![FHIR](https://img.shields.io/badge/FHIR-R4-orange) ![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red) ![License](https://img.shields.io/badge/License-MIT-yellow)

> Parse synthetic FHIR R4 patient bundles (Synthea) and generate clinical analytics: population health summaries, condition prevalence, medication trends, and care gap analysis.

---

## Overview

FHIR (Fast Healthcare Interoperability Resources) is the modern standard for clinical data exchange. This tool:
1. **Ingests** Synthea-generated synthetic FHIR R4 JSON bundles
2. **Parses** key clinical resources: Patient, Condition, MedicationRequest, Observation, Encounter
3. **Analyzes** population-level health trends
4. **Visualizes** results via an interactive Streamlit dashboard

Relevant for biomedical informatics applications, EHR analytics, and clinical data science roles.

---

## Dataset: Synthea

[Synthea](https://github.com/synthetichealth/synthea) generates realistic, de-identified synthetic patient data in FHIR format. Generate your own:

```bash
# Install and run Synthea
java -jar synthea-with-dependencies.jar -p 1000 Massachusetts
```

Or download pre-generated samples from the [Synthea wiki](https://github.com/synthetichealth/synthea/wiki/Sample-Data).

---

## Installation

```bash
git clone https://github.com/hollyakt/fhir-parser.git
cd fhir-parser
pip install -r requirements.txt
```

---

## Usage

```bash
# Parse a directory of FHIR JSON files
python src/parse.py --input data/synthea/ --output data/parsed/

# Generate analytics
python src/analyze.py --data data/parsed/ --output results/

# Launch Streamlit dashboard
streamlit run app/dashboard.py
```

---

## Features

- **Demographics**: Age/sex distribution, insurance coverage, geographic spread
- **Conditions**: Top diagnoses by prevalence, ICD-10 mapping, comorbidity analysis
- **Medications**: Most prescribed drugs, polypharmacy detection
- **Encounters**: Care setting utilization (ED, inpatient, outpatient)
- **Labs**: Abnormal value detection, trend analysis
- **Care gaps**: Patients overdue for preventive screenings

---

## Project Structure

```
fhir-parser/
├── src/
│   ├── parser.py     # FHIR bundle parser
│   ├── analyze.py    # Population analytics
│   └── models.py     # Pydantic data models
├── app/
│   └── dashboard.py  # Streamlit analytics dashboard
├── data/sample/      # Sample FHIR JSON files
├── notebooks/
│   └── 01_fhir_analytics.ipynb
├── requirements.txt
└── README.md
```

---

## License

MIT License.
