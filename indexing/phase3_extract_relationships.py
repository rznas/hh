"""
Phase 3: Extract relationships between medical entities.

This script creates relationships between:
- Disease → Symptom (presents_with)
- Disease → Sign (associated_with)
- Disease → Treatment (treated_with)
- Symptom/Sign → Disease (differential_diagnosis)
- Disease → Diagnostic Test (diagnosed_with)

Input:
- Phase 2 outputs: diseases.json, symptoms.json, signs.json, treatments.json, diagnostic_tests.json
- Phase 1 outputs: wills_eye_text_blocks.json, differential_diagnoses.json

Output:
- graphrag_edges.json (all relationships)
- phase3_report.json (extraction statistics)
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

# Paths
PHASE1_DIR = Path(__file__).parent / "output" / "phase1"
PHASE2_DIR = Path(__file__).parent / "output" / "phase2"
PHASE3_DIR = Path(__file__).parent / "output" / "phase3"

# Create output directory
PHASE3_DIR.mkdir(parents=True, exist_ok=True)


def load_entities() -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
    """Load all Phase 2 entities."""
    with open(PHASE2_DIR / "diseases.json", encoding="utf-8") as f:
        diseases = json.load(f)
    with open(PHASE2_DIR / "symptoms.json", encoding="utf-8") as f:
        symptoms = json.load(f)
    with open(PHASE2_DIR / "signs.json", encoding="utf-8") as f:
        signs = json.load(f)
    with open(PHASE2_DIR / "treatments.json", encoding="utf-8") as f:
        treatments = json.load(f)
    with open(PHASE2_DIR / "diagnostic_tests.json", encoding="utf-8") as f:
        tests = json.load(f)

    return diseases, symptoms, signs, treatments, tests


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        # If it's already a list, return it; otherwise get from 'text_blocks' key
        return data if isinstance(data, list) else data.get("text_blocks", [])


def load_differential_diagnoses() -> List[Dict]:
    """Load Phase 1 differential diagnosis structures."""
    with open(PHASE1_DIR / "differential_diagnoses.json", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("differential_diagnoses", [])


def create_entity_lookup(entities: List[Dict]) -> Dict[str, Dict]:
    """Create lookup dictionary for entities by normalized name."""
    lookup = {}
    for entity in entities:
        normalized = entity.get("name_normalized", entity["name"].lower())
        lookup[normalized] = entity
    return lookup


def extract_disease_symptom_relationships(
    diseases: List[Dict],
    symptoms: List[Dict],
    text_blocks: List[Dict]
) -> List[Dict]:
    """Extract Disease → Symptom (presents_with) relationships."""
    relationships = []
    disease_lookup = create_entity_lookup(diseases)
    symptom_lookup = create_entity_lookup(symptoms)

    # Create symptom keyword patterns
    symptom_patterns = {}
    for symptom in symptoms:
        name = symptom["name"].lower()
        # Create variations
        patterns = [
            name,
            name + "s",  # plural
            name.replace(" ", "-"),  # hyphenated
        ]
        symptom_patterns[symptom["entity_id"]] = patterns

    # Search for co-occurrences in text blocks
    for block in text_blocks:
        text = block.get("text", "").lower()
        chapter = block.get("chapter_number")

        # Find diseases in text
        for disease in diseases:
            disease_name = disease["name"].lower()
            if disease_name in text and len(disease_name) > 4:  # Avoid short matches
                # Find symptoms in same text
                for symptom in symptoms:
                    for pattern in symptom_patterns[symptom["entity_id"]]:
                        if pattern in text and len(pattern) > 3:
                            # Create relationship
                            rel = {
                                "source": disease["entity_id"],
                                "target": symptom["entity_id"],
                                "relationship_type": "presents_with",
                                "description": f"{disease['name']} presents with {symptom['name']}",
                                "weight": 0.7,
                                "metadata": {
                                    "chapter": chapter,
                                    "extraction_method": "co-occurrence"
                                }
                            }
                            relationships.append(rel)
                            break  # Avoid duplicates

    return relationships


def extract_disease_sign_relationships(
    diseases: List[Dict],
    signs: List[Dict],
    text_blocks: List[Dict]
) -> List[Dict]:
    """Extract Disease → Sign (associated_with) relationships."""
    relationships = []

    # Create sign keyword patterns
    sign_patterns = {}
    for sign in signs:
        name = sign["name"].lower()
        patterns = [name, name + "s"]
        sign_patterns[sign["entity_id"]] = patterns

    # Search for co-occurrences
    for block in text_blocks:
        text = block.get("text", "").lower()
        chapter = block.get("chapter_number")

        for disease in diseases:
            disease_name = disease["name"].lower()
            if disease_name in text and len(disease_name) > 4:
                for sign in signs:
                    for pattern in sign_patterns[sign["entity_id"]]:
                        if pattern in text and len(pattern) > 3:
                            rel = {
                                "source": disease["entity_id"],
                                "target": sign["entity_id"],
                                "relationship_type": "associated_with",
                                "description": f"{disease['name']} shows sign of {sign['name']}",
                                "weight": 0.7,
                                "metadata": {
                                    "chapter": chapter,
                                    "extraction_method": "co-occurrence"
                                }
                            }
                            relationships.append(rel)
                            break

    return relationships


def extract_disease_treatment_relationships(
    diseases: List[Dict],
    treatments: List[Dict],
    text_blocks: List[Dict]
) -> List[Dict]:
    """Extract Disease → Treatment (treated_with) relationships."""
    relationships = []

    # Focus on treatment sections
    treatment_keywords = ["treatment", "management", "therapy", "medication"]

    for block in text_blocks:
        text = block.get("text", "").lower()
        chapter = block.get("chapter_number")
        section = block.get("section_title", "").lower()

        # Check if this is a treatment-related section
        is_treatment_section = any(kw in section for kw in treatment_keywords)

        if is_treatment_section or any(kw in text for kw in treatment_keywords):
            for disease in diseases:
                disease_name = disease["name"].lower()
                if disease_name in text and len(disease_name) > 4:
                    for treatment in treatments:
                        treatment_name = treatment["name"].lower()
                        if treatment_name in text and len(treatment_name) > 3:
                            # Higher weight for treatment sections
                            weight = 0.8 if is_treatment_section else 0.6

                            rel = {
                                "source": disease["entity_id"],
                                "target": treatment["entity_id"],
                                "relationship_type": "treated_with",
                                "description": f"{disease['name']} treated with {treatment['name']}",
                                "weight": weight,
                                "metadata": {
                                    "chapter": chapter,
                                    "treatment_type": treatment.get("type"),
                                    "extraction_method": "co-occurrence"
                                }
                            }
                            relationships.append(rel)

    return relationships


def extract_differential_diagnosis_relationships(
    diseases: List[Dict],
    ddx_data: List[Dict]
) -> List[Dict]:
    """Extract Differential Diagnosis relationships from structured DDx data."""
    relationships = []
    disease_lookup = create_entity_lookup(diseases)

    for ddx in ddx_data:
        presenting_complaint = ddx.get("presenting_complaint", "")
        chapter = ddx.get("chapter_number")

        # Extract diseases from DDx list
        for item in ddx.get("differential_diagnoses", []):
            disease_text = item.get("disease", "")

            # Clean disease name (remove cross-references)
            clean_disease = re.sub(r'\(see.*?\)', '', disease_text).strip()
            clean_disease = clean_disease.rstrip('.,;')

            # Find matching disease entity
            normalized = clean_disease.lower()
            if normalized in disease_lookup:
                disease_entity = disease_lookup[normalized]

                # Create relationship
                # This is a reverse relationship: symptom/sign suggests disease
                rel = {
                    "source": disease_entity["entity_id"],
                    "target": presenting_complaint,  # Will need to map to entity
                    "relationship_type": "differential_diagnosis",
                    "description": f"{clean_disease} in differential for {presenting_complaint}",
                    "weight": 0.9,  # High confidence from structured data
                    "metadata": {
                        "chapter": chapter,
                        "rank": item.get("rank"),
                        "extraction_method": "structured_ddx"
                    }
                }
                relationships.append(rel)

    return relationships


def extract_disease_test_relationships(
    diseases: List[Dict],
    tests: List[Dict],
    text_blocks: List[Dict]
) -> List[Dict]:
    """Extract Disease → Diagnostic Test (diagnosed_with) relationships."""
    relationships = []

    # Diagnostic keywords
    diagnostic_keywords = ["test", "exam", "imaging", "workup", "evaluation"]

    for block in text_blocks:
        text = block.get("text", "").lower()
        chapter = block.get("chapter_number")
        section = block.get("section_title", "").lower()

        is_diagnostic_section = any(kw in section for kw in diagnostic_keywords)

        if is_diagnostic_section or any(kw in text for kw in diagnostic_keywords):
            for disease in diseases:
                disease_name = disease["name"].lower()
                if disease_name in text and len(disease_name) > 4:
                    for test in tests:
                        test_name = test["name"].lower()
                        if test_name in text and len(test_name) > 3:
                            weight = 0.8 if is_diagnostic_section else 0.6

                            rel = {
                                "source": disease["entity_id"],
                                "target": test["entity_id"],
                                "relationship_type": "diagnosed_with",
                                "description": f"{disease['name']} diagnosed with {test['name']}",
                                "weight": weight,
                                "metadata": {
                                    "chapter": chapter,
                                    "test_type": test.get("type"),
                                    "extraction_method": "co-occurrence"
                                }
                            }
                            relationships.append(rel)

    return relationships


def deduplicate_relationships(relationships: List[Dict]) -> List[Dict]:
    """Remove duplicate relationships, keeping highest weight."""
    seen = {}

    for rel in relationships:
        key = (rel["source"], rel["target"], rel["relationship_type"])

        if key not in seen or rel["weight"] > seen[key]["weight"]:
            seen[key] = rel

    return list(seen.values())


def main():
    """Main execution function."""
    print("=" * 60)
    print("Phase 3: Relationship Extraction")
    print("=" * 60)

    # Load entities
    print("\n[1/7] Loading Phase 2 entities...")
    diseases, symptoms, signs, treatments, tests = load_entities()
    print(f"  + Loaded {len(diseases)} diseases")
    print(f"  + Loaded {len(symptoms)} symptoms")
    print(f"  + Loaded {len(signs)} signs")
    print(f"  + Loaded {len(treatments)} treatments")
    print(f"  + Loaded {len(tests)} diagnostic tests")

    # Load Phase 1 data
    print("\n[2/7] Loading Phase 1 data...")
    text_blocks = load_text_blocks()
    ddx_data = load_differential_diagnoses()
    print(f"  + Loaded {len(text_blocks)} text blocks")
    print(f"  + Loaded {len(ddx_data)} differential diagnosis lists")

    # Extract relationships
    all_relationships = []

    print("\n[3/7] Extracting Disease -> Symptom relationships...")
    disease_symptom = extract_disease_symptom_relationships(diseases, symptoms, text_blocks)
    print(f"  + Extracted {len(disease_symptom)} relationships")
    all_relationships.extend(disease_symptom)

    print("\n[4/7] Extracting Disease -> Sign relationships...")
    disease_sign = extract_disease_sign_relationships(diseases, signs, text_blocks)
    print(f"  + Extracted {len(disease_sign)} relationships")
    all_relationships.extend(disease_sign)

    print("\n[5/7] Extracting Disease -> Treatment relationships...")
    disease_treatment = extract_disease_treatment_relationships(diseases, treatments, text_blocks)
    print(f"  + Extracted {len(disease_treatment)} relationships")
    all_relationships.extend(disease_treatment)

    print("\n[6/7] Extracting Differential Diagnosis relationships...")
    ddx_relationships = extract_differential_diagnosis_relationships(diseases, ddx_data)
    print(f"  + Extracted {len(ddx_relationships)} relationships")
    all_relationships.extend(ddx_relationships)

    print("\n[7/7] Extracting Disease -> Diagnostic Test relationships...")
    disease_test = extract_disease_test_relationships(diseases, tests, text_blocks)
    print(f"  + Extracted {len(disease_test)} relationships")
    all_relationships.extend(disease_test)

    # Deduplicate
    print("\n[8/8] Deduplicating relationships...")
    unique_relationships = deduplicate_relationships(all_relationships)
    print(f"  + Removed {len(all_relationships) - len(unique_relationships)} duplicates")
    print(f"  + Final count: {len(unique_relationships)} relationships")

    # Save output
    output_file = PHASE3_DIR / "graphrag_edges.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_relationships, f, indent=2)
    print(f"\n+ Saved to: {output_file}")

    # Generate report
    report = {
        "total_relationships": len(unique_relationships),
        "by_type": {
            "presents_with": len([r for r in unique_relationships if r["relationship_type"] == "presents_with"]),
            "associated_with": len([r for r in unique_relationships if r["relationship_type"] == "associated_with"]),
            "treated_with": len([r for r in unique_relationships if r["relationship_type"] == "treated_with"]),
            "differential_diagnosis": len([r for r in unique_relationships if r["relationship_type"] == "differential_diagnosis"]),
            "diagnosed_with": len([r for r in unique_relationships if r["relationship_type"] == "diagnosed_with"]),
        },
        "statistics": {
            "avg_weight": sum(r["weight"] for r in unique_relationships) / len(unique_relationships),
            "high_confidence": len([r for r in unique_relationships if r["weight"] >= 0.8]),
            "medium_confidence": len([r for r in unique_relationships if 0.6 <= r["weight"] < 0.8]),
            "low_confidence": len([r for r in unique_relationships if r["weight"] < 0.6]),
        }
    }

    report_file = PHASE3_DIR / "phase3_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"+ Report saved to: {report_file}")

    print("\n" + "=" * 60)
    print("Phase 3 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
