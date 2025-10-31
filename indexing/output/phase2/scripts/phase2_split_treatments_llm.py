#!/usr/bin/env python3
"""
Phase 2 Compensation: Split TREATMENT into MEDICATION + PROCEDURE using LLM (Issue 1.1)

LLM-enhanced classification of treatments into medications and procedures.

Input: Phase 2: treatments.json
Output: medications_llm.json, procedures_llm.json

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_split_treatments_llm.py
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from openai import OpenAI
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).parent
PHASE2_DIR = SCRIPT_DIR.parent
INPUT_FILE = PHASE2_DIR / "treatments.json"
MEDICATIONS_FILE = PHASE2_DIR / "medications_llm.json"
PROCEDURES_FILE = PHASE2_DIR / "procedures_llm.json"
REPORT_FILE = PHASE2_DIR / "phase2_treatment_split_llm_report.json"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiI2OTAyNTk3MWYwN2ViNTczMjgzZmIxMjkiLCJ0eXBlIjoiYWlfa2V5IiwiaWF0IjoxNzYxNzYxNjQ5fQ.Wllnd6Fn-fghYv1uk18ZoXNXHDRw30vDiEwNBQXUqR8")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://ai.liara.ir/api/68721419652cec5504661aec/v1")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "anthropic/claude-sonnet-4.5")

for var in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"]:
    os.environ.pop(var, None)

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=None)


CLASSIFICATION_PROMPT = """You are classifying a medical treatment entity as either MEDICATION or PROCEDURE.

**Definitions:**
- MEDICATION: Drugs, pharmaceuticals, topical agents, oral medications, injections (e.g., "antibiotic drops", "steroid ointment", "oral prednisone")
- PROCEDURE: Surgeries, examinations, tests, interventions, physical therapies (e.g., "vitrectomy", "laser photocoagulation", "slit lamp exam", "warm compresses")

**Treatment to classify:**
Name: {name}
Description: {description}

**Your task:** Classify this treatment as either "MEDICATION" or "PROCEDURE". Consider the nature of the intervention."""

CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["MEDICATION", "PROCEDURE"],
            "description": "Classification result"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence in classification"
        }
    },
    "required": ["classification", "confidence"],
    "additionalProperties": False
}


def load_treatments() -> List[Dict]:
    if not INPUT_FILE.exists():
        print(f"❌ {INPUT_FILE} not found")
        return []
    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def classify_treatment_with_llm(treatment: Dict) -> str:
    """Classify treatment using LLM. Returns 'medication' or 'procedure'."""
    name = treatment.get("name", "")
    description = treatment.get("description", "")

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            max_tokens=100,
            temperature=0.0,
            messages=[{"role": "user", "content": CLASSIFICATION_PROMPT.format(name=name, description=description)}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "treatment_classification",
                    "strict": True,
                    "schema": CLASSIFICATION_SCHEMA
                }
            }
        )

        result = json.loads(response.choices[0].message.content.strip())
        classification = result.get("classification", "PROCEDURE").lower()
        return classification

    except Exception as e:
        print(f"  ⚠ Error classifying {name}: {e}")
        return "procedure"  # Default to procedure on error


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2: Split TREATMENT → MEDICATION + PROCEDURE (LLM)")
    print("=" * 80)

    treatments = load_treatments()
    if not treatments:
        return

    print(f"  ✓ Loaded {len(treatments)} treatments")

    if args.dry_run:
        print("\n[DRY RUN] Sample classification:")
        sample = treatments[0]
        print(CLASSIFICATION_PROMPT.format(
            name=sample.get("name", ""),
            description=sample.get("description", "")
        ))
        return

    print("\n[2/3] Classifying with LLM...")
    medications = []
    procedures = []

    for treatment in tqdm(treatments, desc="  Classifying"):
        classification = classify_treatment_with_llm(treatment)

        treatment_copy = treatment.copy()
        if classification == "medication":
            treatment_copy["type"] = "medication"
            treatment_copy["entity_id"] = f"medication_{len(medications)+1:03d}"
            medications.append(treatment_copy)
        else:
            treatment_copy["type"] = "procedure"
            treatment_copy["entity_id"] = f"procedure_{len(procedures)+1:03d}"
            procedures.append(treatment_copy)

    print(f"  ✓ Medications: {len(medications)}")
    print(f"  ✓ Procedures: {len(procedures)}")

    print("\n[3/3] Saving...")
    with open(MEDICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(medications, f, indent=2, ensure_ascii=False)
    with open(PROCEDURES_FILE, "w", encoding="utf-8") as f:
        json.dump(procedures, f, indent=2, ensure_ascii=False)

    report = {
        "method": "llm_classification",
        "total": len(treatments),
        "medications": len(medications),
        "procedures": len(procedures)
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"✓ Done: {len(medications)} medications, {len(procedures)} procedures")


if __name__ == "__main__":
    main()
