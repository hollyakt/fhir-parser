"""
FHIR R4 Bundle Parser for Synthea-generated patient data.

Parses FHIR resources: Patient, Condition, MedicationRequest,
Observation, Encounter into flat pandas DataFrames for analytics.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date

import pandas as pd
from tqdm import tqdm


def safe_get(obj: dict, *keys, default=None):
    """Safely traverse nested dict keys."""
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k, default)
        if obj is None:
            return default
    return obj


def parse_patient(resource: dict) -> dict:
    """Extract key fields from a FHIR Patient resource."""
    birth_date = resource.get("birthDate", "")
    age = None
    if birth_date:
        try:
            bd = datetime.strptime(birth_date, "%Y-%m-%d").date()
            age = (date.today() - bd).days // 365
        except ValueError:
            pass

    return {
        "patient_id": resource.get("id", ""),
        "gender": resource.get("gender", "unknown"),
        "birth_date": birth_date,
        "age": age,
        "city": safe_get(resource, "address", 0, "city") or "",
        "state": safe_get(resource, "address", 0, "state") or "",
        "marital_status": safe_get(resource, "maritalStatus", "text") or "",
        "deceased": resource.get("deceasedBoolean", False),
    }


def parse_condition(resource: dict) -> dict:
    """Extract key fields from a FHIR Condition resource."""
    coding = safe_get(resource, "code", "coding", 0) or {}
    return {
        "patient_id": safe_get(resource, "subject", "reference", default="").replace("urn:uuid:", ""),
        "condition_id": resource.get("id", ""),
        "code": coding.get("code", ""),
        "display": coding.get("display", ""),
        "system": coding.get("system", ""),
        "onset_date": resource.get("onsetDateTime", "")[:10] if resource.get("onsetDateTime") else "",
        "clinical_status": safe_get(resource, "clinicalStatus", "coding", 0, "code") or "",
        "category": safe_get(resource, "category", 0, "coding", 0, "display") or "",
    }


def parse_medication_request(resource: dict) -> dict:
    """Extract key fields from a FHIR MedicationRequest resource."""
    med_coding = safe_get(resource, "medicationCodeableConcept", "coding", 0) or {}
    return {
        "patient_id": safe_get(resource, "subject", "reference", default="").replace("urn:uuid:", ""),
        "med_id": resource.get("id", ""),
        "med_code": med_coding.get("code", ""),
        "med_name": med_coding.get("display", ""),
        "status": resource.get("status", ""),
        "authored_on": resource.get("authoredOn", "")[:10] if resource.get("authoredOn") else "",
        "intent": resource.get("intent", ""),
    }


def parse_observation(resource: dict) -> dict:
    """Extract key fields from a FHIR Observation resource."""
    coding = safe_get(resource, "code", "coding", 0) or {}
    value = resource.get("valueQuantity", {})
    return {
        "patient_id": safe_get(resource, "subject", "reference", default="").replace("urn:uuid:", ""),
        "obs_id": resource.get("id", ""),
        "code": coding.get("code", ""),
        "display": coding.get("display", ""),
        "value": value.get("value"),
        "unit": value.get("unit", ""),
        "effective_date": resource.get("effectiveDateTime", "")[:10] if resource.get("effectiveDateTime") else "",
        "status": resource.get("status", ""),
    }


def parse_encounter(resource: dict) -> dict:
    """Extract key fields from a FHIR Encounter resource."""
    type_coding = safe_get(resource, "type", 0, "coding", 0) or {}
    class_code = safe_get(resource, "class", "code") or ""
    period = resource.get("period", {})
    return {
        "patient_id": safe_get(resource, "subject", "reference", default="").replace("urn:uuid:", ""),
        "encounter_id": resource.get("id", ""),
        "class": class_code,
        "type": type_coding.get("display", ""),
        "status": resource.get("status", ""),
        "start": period.get("start", "")[:10] if period.get("start") else "",
        "end": period.get("end", "")[:10] if period.get("end") else "",
    }


RESOURCE_PARSERS = {
    "Patient": parse_patient,
    "Condition": parse_condition,
    "MedicationRequest": parse_medication_request,
    "Observation": parse_observation,
    "Encounter": parse_encounter,
}


def parse_bundle(bundle: dict) -> Dict[str, List[dict]]:
    """
    Parse a FHIR Bundle and extract all supported resource types.

    Args:
        bundle: Parsed FHIR Bundle JSON (dict).

    Returns:
        Dict mapping resource type → list of parsed record dicts.
    """
    records = {rt: [] for rt in RESOURCE_PARSERS}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType", "")
        if rtype in RESOURCE_PARSERS:
            try:
                parsed = RESOURCE_PARSERS[rtype](resource)
                records[rtype].append(parsed)
            except Exception:
                pass
    return records


def parse_directory(input_dir: str, output_dir: str = None) -> Dict[str, pd.DataFrame]:
    """
    Parse all FHIR JSON files in a directory.

    Args:
        input_dir:  Directory of Synthea FHIR JSON files.
        output_dir: If provided, save DataFrames as CSV files.

    Returns:
        Dict of {resource_type: DataFrame}.
    """
    input_dir = Path(input_dir)
    json_files = list(input_dir.glob("*.json"))
    print(f"Found {len(json_files)} FHIR JSON files")

    all_records = {rt: [] for rt in RESOURCE_PARSERS}

    for fpath in tqdm(json_files, desc="Parsing FHIR bundles"):
        try:
            with open(fpath) as f:
                bundle = json.load(f)
            records = parse_bundle(bundle)
            for rtype, recs in records.items():
                all_records[rtype].extend(recs)
        except Exception as e:
            print(f"  Error parsing {fpath.name}: {e}")

    dfs = {}
    for rtype, records in all_records.items():
        if records:
            dfs[rtype] = pd.DataFrame(records)
            print(f"  {rtype}: {len(records)} records")

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for rtype, df in dfs.items():
            df.to_csv(output_dir / f"{rtype.lower()}.csv", index=False)
        print(f"Saved to {output_dir}")

    return dfs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default="data/parsed")
    args = parser.parse_args()
    parse_directory(args.input, args.output)
