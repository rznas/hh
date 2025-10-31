#!/usr/bin/env python3
"""
Phase 2 Compensation: Split TREATMENT into MEDICATION + PROCEDURE (Issue 1.1)

This script implements the baseline (non-LLM) approach for splitting existing treatment
entities into separate medication and procedure categories.

Approach:
- Load existing treatments.json
- Classify each treatment using keyword matching
- Generate separate medications.json and procedures.json files

Classification Rules:
- MEDICATION: drugs, drops, ointments, injections, topical/oral/IV medications
- PROCEDURE: surgeries, examinations, tests, interventions, therapies

Input:
- Phase 2: treatments.json (existing merged treatments)

Output:
- medications.json (medication entities)
- procedures.json (procedure entities)
- phase2_treatment_split_report.json (split statistics)

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_split_treatments.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_split_treatments.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE2_DIR = SCRIPT_DIR.parent
INPUT_FILE = PHASE2_DIR / "treatments.json"
MEDICATIONS_FILE = PHASE2_DIR / "medications.json"
PROCEDURES_FILE = PHASE2_DIR / "procedures.json"
REPORT_FILE = PHASE2_DIR / "phase2_treatment_split_report.json"

# Medication keywords (drugs, routes, formulations)
MEDICATION_KEYWORDS = [
    # Drug classes
    "antibiotic", "antiviral", "antifungal", "steroid", "nsaid",
    "antihistamine", "mydriatic", "cycloplegic", "miotic",
    "beta-blocker", "alpha-agonist", "carbonic anhydrase inhibitor",
    "prostaglandin analog", "immunosuppressant", "analgesic",

    # Formulations
    "drops", "ointment", "gel", "solution", "suspension",
    "tablet", "capsule", "injection", "implant",

    # Routes
    "topical", "oral", "intravenous", "intravitreal", "subconjunctival",
    "systemic", "iv", "po", "ophthalmic",

    # Specific drug suffixes
    "mycin", "cillin", "cycline", "floxacin", "zole", "olone",
    "oprost", "olol", "idine", "pine",

    # Common terms
    "medication", "drug", "pharmaceutical", "therapeutic agent"
]

# Procedure keywords (surgeries, interventions, tests)
PROCEDURE_KEYWORDS = [
    # Surgeries
    "surgery", "surgical", "operation", "excision", "incision",
    "cryotherapy", "laser", "photocoagulation", "vitrectomy",
    "keratoplasty", "transplant", "graft", "suture",
    "trabeculectomy", "iridotomy", "capsulotomy",
    "phacoemulsification", "extraction", "implantation",

    # Interventions
    "injection", "debridement", "drainage", "aspiration",
    "cauterization", "punctal plug", "occlusion",

    # Examinations/Tests
    "examination", "test", "imaging", "scan", "ultrasound",
    "oct", "fluorescein angiography", "fundus photography",
    "tonometry", "pachymetry", "biometry", "perimetry",
    "visual field", "electroretinography", "erg",
    "slit lamp", "gonioscopy", "ophthalmoscopy",
    "biomicroscopy", "indentation", "b-scan",

    # General
    "procedure", "intervention", "technique", "therapy",
    "treatment", "management", "monitoring"
]

# Special cases (explicit classification)
MEDICATION_EXPLICIT = {
    "artificial tears", "lubricating drops", "preservative-free drops",
    "antibiotic drops", "steroid drops", "pressure-lowering drops",
    "cyclosporine", "tacrolimus", "mycophenolate",
    "prednisone", "prednisolone", "dexamethasone",
    "azithromycin", "erythromycin", "bacitracin",
    "ganciclovir", "acyclovir", "valacyclovir"
}

PROCEDURE_EXPLICIT = {
    "warm compresses", "lid hygiene", "lid scrubs",
    "follow up", "observation", "monitoring",
    "patching", "bandage contact lens",
    "referral", "consultation"
}


def load_treatments() -> List[Dict]:
    """Load existing treatment entities."""
    if not INPUT_FILE.exists():
        print(f"❌ Error: {INPUT_FILE} not found")
        return []

    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def classify_treatment(treatment: Dict) -> str:
    """
    Classify a treatment entity as MEDICATION or PROCEDURE.
    Returns: "medication" or "procedure"
    """
    name = treatment.get("name", "").lower()
    description = treatment.get("description", "").lower()
    text = f"{name} {description}"

    # Check explicit classifications first
    if name in MEDICATION_EXPLICIT:
        return "medication"
    if name in PROCEDURE_EXPLICIT:
        return "procedure"

    # Score based on keyword matches
    medication_score = 0
    procedure_score = 0

    for keyword in MEDICATION_KEYWORDS:
        if keyword.lower() in text:
            medication_score += 1

    for keyword in PROCEDURE_KEYWORDS:
        if keyword.lower() in text:
            procedure_score += 1

    # Pattern-based classification
    # Check for drug name patterns (e.g., ends with -mycin, -olone, etc.)
    drug_pattern = r'\b\w+(mycin|cillin|cycline|floxacin|zole|olone|oprost|olol|idine)\b'
    if re.search(drug_pattern, name):
        medication_score += 2

    # Check for procedure patterns
    procedure_pattern = r'\b(perform|undergo|receive)\s+(a|an|the)?\s*\w+'
    if re.search(procedure_pattern, text):
        procedure_score += 1

    # Surgery/intervention indicators
    if any(word in name for word in ["surgery", "surgical", "-ectomy", "-tomy", "-plasty"]):
        procedure_score += 3

    # Medication indicators
    if any(word in name for word in ["drops", "ointment", "tablet", "mg", "dose"]):
        medication_score += 2

    # Decide based on scores
    if medication_score > procedure_score:
        return "medication"
    elif procedure_score > medication_score:
        return "procedure"
    else:
        # Default: if contains "drops", "ointment", "oral" -> medication
        # else -> procedure
        if any(word in name for word in ["drops", "ointment", "oral", "topical"]):
            return "medication"
        return "procedure"


def create_entity_id(entity_type: str, index: int) -> str:
    """Generate entity ID based on type."""
    return f"{entity_type}_{index:03d}"


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Split treatments into medications and procedures")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: Split TREATMENT → MEDICATION + PROCEDURE")
    print("=" * 80)
    print(f"Method: Keyword matching + pattern classification")
    print(f"Input: {INPUT_FILE}")
    print("=" * 80)

    # Load treatments
    print("\n[1/3] Loading existing treatments...")
    treatments = load_treatments()

    if not treatments:
        print("❌ No treatments found. Exiting.")
        return

    print(f"  ✓ Loaded {len(treatments)} treatment entities")

    # Classify treatments
    print("\n[2/3] Classifying treatments...")
    medications = []
    procedures = []

    for treatment in treatments:
        classification = classify_treatment(treatment)

        # Update type field
        treatment_copy = treatment.copy()

        if classification == "medication":
            treatment_copy["type"] = "medication"
            medications.append(treatment_copy)
        else:
            treatment_copy["type"] = "procedure"
            procedures.append(treatment_copy)

    print(f"  ✓ Classified {len(medications)} as medications")
    print(f"  ✓ Classified {len(procedures)} as procedures")

    # Re-assign entity IDs
    for idx, med in enumerate(medications, 1):
        med["entity_id"] = create_entity_id("medication", idx)

    for idx, proc in enumerate(procedures, 1):
        proc["entity_id"] = create_entity_id("procedure", idx)

    # Show samples
    print("\n  Sample medications:")
    for med in medications[:5]:
        print(f"    • {med['name']}")

    print("\n  Sample procedures:")
    for proc in procedures[:5]:
        print(f"    • {proc['name']}")

    if args.dry_run:
        print("\n[DRY RUN] Would save:")
        print(f"  • {MEDICATIONS_FILE} ({len(medications)} entities)")
        print(f"  • {PROCEDURES_FILE} ({len(procedures)} entities)")
        return

    # Save files
    print("\n[3/3] Saving split files...")

    with open(MEDICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(medications, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(medications)} medications to {MEDICATIONS_FILE}")

    with open(PROCEDURES_FILE, "w", encoding="utf-8") as f:
        json.dump(procedures, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(procedures)} procedures to {PROCEDURES_FILE}")

    # Generate report
    report = {
        "split_method": "baseline_keyword_classification",
        "input_file": str(INPUT_FILE),
        "total_treatments": len(treatments),
        "medications_count": len(medications),
        "procedures_count": len(procedures),
        "medication_percentage": round(len(medications) / len(treatments) * 100, 1),
        "procedure_percentage": round(len(procedures) / len(treatments) * 100, 1),
        "medication_keywords_used": len(MEDICATION_KEYWORDS),
        "procedure_keywords_used": len(PROCEDURE_KEYWORDS),
        "top_medications": [
            {"name": m["name"], "id": m["entity_id"]}
            for m in medications[:10]
        ],
        "top_procedures": [
            {"name": p["name"], "id": p["entity_id"]}
            for p in procedures[:10]
        ]
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved report to {REPORT_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("SPLIT SUMMARY")
    print("=" * 80)
    print(f"Total Treatments: {len(treatments)}")
    print(f"  → Medications: {len(medications)} ({report['medication_percentage']}%)")
    print(f"  → Procedures: {len(procedures)} ({report['procedure_percentage']}%)")
    print("=" * 80)


if __name__ == "__main__":
    main()
