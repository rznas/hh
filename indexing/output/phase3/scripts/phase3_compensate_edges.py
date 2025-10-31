#!/usr/bin/env python3
"""
Phase 3 Compensation: Extract missing edge types (Issues 2.2, 2.4, 2.7, 2.8)

This script creates missing relationship types using baseline pattern matching:
- caused_by (Disease → Etiology)
- affects (Disease → Anatomy)
- increases_risk (Risk Factor → Disease)
- contraindicates (Condition → Treatment) - CRITICAL for medical safety

Approach:
- Load entities from Phase 2 (diseases, etiologies, anatomy, risk_factors, treatments)
- Pattern matching in text blocks to find relationships
- Generate relationship edges with confidence scores

Input:
- Phase 1: wills_eye_text_blocks.json
- Phase 2: diseases.json, etiology.json, anatomy.json, risk_factors.json, treatments.json, medications.json, procedures.json

Output:
- caused_by_edges.json
- affects_edges.json
- increases_risk_edges.json
- contraindicates_edges.json
- phase3_compensation_report.json

Usage:
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_edges.py
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_edges.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent.parent / "phase2"
PHASE3_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PHASE3_DIR

# Relationship patterns
CAUSED_BY_PATTERNS = [
    r"(\w[\w\s]+?)\s+(?:is\s+)?caused by\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+due to\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+secondary to\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+resulting from\s+([^.;,]+)",
]

AFFECTS_PATTERNS = [
    r"(\w[\w\s]+?)\s+affects?\s+(?:the\s+)?([^.;,]+)",
    r"(\w[\w\s]+?)\s+involving\s+(?:the\s+)?([^.;,]+)",
    r"(\w[\w\s]+?)\s+of\s+the\s+([^.;,]+)",
]

INCREASES_RISK_PATTERNS = [
    r"([^.;,]+?)\s+increases?\s+(?:the\s+)?risk\s+(?:of\s+|for\s+)?([^.;,]+)",
    r"([^.;,]+?)\s+(?:is\s+a\s+)?risk\s+factor\s+for\s+([^.;,]+)",
    r"([^.;,]+?)\s+predisposes?\s+to\s+([^.;,]+)",
]

CONTRAINDICATES_PATTERNS = [
    r"contraindicated\s+in\s+([^.;,]+)",
    r"avoid\s+([^.;,]+)\s+in\s+(?:patients\s+with\s+)?([^.;,]+)",
    r"do not use\s+([^.;,]+)\s+(?:in|with)\s+([^.;,]+)",
    r"([^.;,]+)\s+should not be used\s+in\s+([^.;,]+)",
]


@dataclass
class Edge:
    """Represents a relationship edge."""
    source: str  # Entity ID
    target: str  # Entity ID
    relationship_type: str
    confidence: float = 0.8
    context: str = ""
    chapter: int = 0

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "target": self.target,
            "relationship_type": self.relationship_type,
            "confidence": self.confidence,
            "context": self.context[:200],
            "metadata": {
                "chapter": self.chapter,
                "extraction_method": "pattern_matching"
            }
        }


def load_entities(entity_type: str) -> Dict[str, Dict]:
    """Load entities and create name->entity map."""
    file_path = PHASE2_DIR / f"{entity_type}.json"

    if not file_path.exists():
        print(f"  ⚠ {entity_type}.json not found, skipping")
        return {}

    with open(file_path, encoding="utf-8") as f:
        entities = json.load(f)

    # Create normalized name -> entity map
    entity_map = {}
    for entity in entities:
        name = entity.get("name", "").lower()
        normalized = entity.get("name_normalized", name)
        entity_map[normalized] = entity
        entity_map[name] = entity

    return entity_map


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def normalize_entity_mention(mention: str) -> str:
    """Normalize entity mention for matching."""
    normalized = mention.lower().strip()
    normalized = re.sub(r'^(a|an|the)\s+', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def find_entity_by_mention(mention: str, entity_map: Dict[str, Dict]) -> str:
    """Find entity ID by mention text."""
    normalized = normalize_entity_mention(mention)

    # Exact match
    if normalized in entity_map:
        return entity_map[normalized].get("entity_id", "")

    # Partial match (contains)
    for entity_name, entity_data in entity_map.items():
        if normalized in entity_name or entity_name in normalized:
            return entity_data.get("entity_id", "")

    return ""


def extract_caused_by_edges(text: str, chapter: int, diseases: Dict, etiologies: Dict) -> List[Edge]:
    """Extract caused_by relationships."""
    edges = []

    for pattern in CAUSED_BY_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            disease_mention = match.group(1).strip()
            etiology_mention = match.group(2).strip()

            disease_id = find_entity_by_mention(disease_mention, diseases)
            etiology_id = find_entity_by_mention(etiology_mention, etiologies)

            if disease_id and etiology_id:
                edge = Edge(
                    source=disease_id,
                    target=etiology_id,
                    relationship_type="caused_by",
                    confidence=0.8,
                    context=match.group(0),
                    chapter=chapter
                )
                edges.append(edge)

    return edges


def extract_affects_edges(text: str, chapter: int, diseases: Dict, anatomy: Dict) -> List[Edge]:
    """Extract affects relationships."""
    edges = []

    for pattern in AFFECTS_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            disease_mention = match.group(1).strip()
            anatomy_mention = match.group(2).strip()

            disease_id = find_entity_by_mention(disease_mention, diseases)
            anatomy_id = find_entity_by_mention(anatomy_mention, anatomy)

            if disease_id and anatomy_id:
                edge = Edge(
                    source=disease_id,
                    target=anatomy_id,
                    relationship_type="affects",
                    confidence=0.7,
                    context=match.group(0),
                    chapter=chapter
                )
                edges.append(edge)

    return edges


def extract_increases_risk_edges(text: str, chapter: int, risk_factors: Dict, diseases: Dict) -> List[Edge]:
    """Extract increases_risk relationships."""
    edges = []

    for pattern in INCREASES_RISK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            risk_mention = match.group(1).strip()
            disease_mention = match.group(2).strip()

            risk_id = find_entity_by_mention(risk_mention, risk_factors)
            disease_id = find_entity_by_mention(disease_mention, diseases)

            if risk_id and disease_id:
                edge = Edge(
                    source=risk_id,
                    target=disease_id,
                    relationship_type="increases_risk",
                    confidence=0.8,
                    context=match.group(0),
                    chapter=chapter
                )
                edges.append(edge)

    return edges


def extract_contraindicates_edges(text: str, chapter: int, diseases: Dict, treatments: Dict) -> List[Edge]:
    """Extract contraindicates relationships (CRITICAL for medical safety)."""
    edges = []

    for pattern in CONTRAINDICATES_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            # Pattern variations require different group handling
            if "contraindicated in" in match.group(0).lower():
                treatment_mention = match.group(0).split("contraindicated")[0].strip()
                condition_mention = match.group(1).strip()
            else:
                treatment_mention = match.group(1).strip()
                condition_mention = match.group(2).strip() if match.lastindex >= 2 else ""

            treatment_id = find_entity_by_mention(treatment_mention, treatments)
            condition_id = find_entity_by_mention(condition_mention, diseases)

            if treatment_id and condition_id:
                edge = Edge(
                    source=condition_id,
                    target=treatment_id,
                    relationship_type="contraindicates",
                    confidence=0.9,  # High confidence for safety
                    context=match.group(0),
                    chapter=chapter
                )
                edges.append(edge)

    return edges


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract missing edge types (baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3 Compensation: Missing Edge Types Extraction (Baseline)")
    print("=" * 80)
    print("Edge types: caused_by, affects, increases_risk, contraindicates")
    print("=" * 80)

    # Load entities
    print("\n[1/3] Loading entities...")
    diseases = load_entities("diseases")
    etiologies = load_entities("etiology")
    anatomy = load_entities("anatomy")
    risk_factors = load_entities("risk_factors")
    treatments = load_entities("treatments")
    medications = load_entities("medications")
    procedures = load_entities("procedures")

    # Merge treatments with medications and procedures
    treatments.update(medications)
    treatments.update(procedures)

    print(f"  ✓ Diseases: {len(diseases)}")
    print(f"  ✓ Etiologies: {len(etiologies)}")
    print(f"  ✓ Anatomy: {len(anatomy)}")
    print(f"  ✓ Risk Factors: {len(risk_factors)}")
    print(f"  ✓ Treatments: {len(treatments)}")

    # Load text blocks
    text_blocks = load_text_blocks()
    print(f"  ✓ Text blocks: {len(text_blocks)}")

    # Extract relationships
    print("\n[2/3] Extracting relationships...")

    caused_by_edges = []
    affects_edges = []
    increases_risk_edges = []
    contraindicates_edges = []

    for block in text_blocks:
        text = block.get("text", "")
        chapter = block.get("chapter_number", 0)

        if not text or len(text) < 50:
            continue

        # Extract each edge type
        caused_by_edges.extend(extract_caused_by_edges(text, chapter, diseases, etiologies))
        affects_edges.extend(extract_affects_edges(text, chapter, diseases, anatomy))
        increases_risk_edges.extend(extract_increases_risk_edges(text, chapter, risk_factors, diseases))
        contraindicates_edges.extend(extract_contraindicates_edges(text, chapter, diseases, treatments))

    print(f"  ✓ caused_by: {len(caused_by_edges)}")
    print(f"  ✓ affects: {len(affects_edges)}")
    print(f"  ✓ increases_risk: {len(increases_risk_edges)}")
    print(f"  ✓ contraindicates: {len(contraindicates_edges)} ⚠ CRITICAL")

    if args.dry_run:
        print("\n[DRY RUN] Sample edges:")
        if caused_by_edges:
            print(f"\ncaused_by: {caused_by_edges[0].to_dict()}")
        if affects_edges:
            print(f"\naffects: {affects_edges[0].to_dict()}")
        return

    # Save edges
    print("\n[3/3] Saving edges...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "caused_by_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in caused_by_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved caused_by_edges.json")

    with open(OUTPUT_DIR / "affects_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in affects_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved affects_edges.json")

    with open(OUTPUT_DIR / "increases_risk_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in increases_risk_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved increases_risk_edges.json")

    with open(OUTPUT_DIR / "contraindicates_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in contraindicates_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved contraindicates_edges.json")

    # Generate report
    report = {
        "extraction_method": "baseline_pattern_matching",
        "total_edges": len(caused_by_edges) + len(affects_edges) + len(increases_risk_edges) + len(contraindicates_edges),
        "by_type": {
            "caused_by": len(caused_by_edges),
            "affects": len(affects_edges),
            "increases_risk": len(increases_risk_edges),
            "contraindicates": len(contraindicates_edges)
        }
    }

    with open(OUTPUT_DIR / "phase3_compensation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved phase3_compensation_report.json")

    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total New Edges: {report['total_edges']}")
    for edge_type, count in report['by_type'].items():
        print(f"  • {edge_type}: {count}")
    print("=" * 80)


if __name__ == "__main__":
    main()
