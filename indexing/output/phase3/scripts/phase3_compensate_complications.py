#!/usr/bin/env python3
"""
Phase 3 Compensation: Extract complication relationships (Issue 2.9)

This script extracts complicates relationships (Disease → Disease) for disease progressions
and complications using baseline pattern matching.

Approach:
- Pattern matching for complication phrases ("complication of", "can lead to", "may progress to")
- Section detection ("Complications" sections)
- Disease-to-disease relationships

Input:
- Phase 1: wills_eye_text_blocks.json
- Phase 2: diseases.json

Output:
- complicates_edges.json
- phase3_complications_report.json

Usage:
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_complications.py
    .venv/bin/python indexing/output/phase3/scripts/phase3_compensate_complications.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent.parent / "phase2"
PHASE3_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PHASE3_DIR

# Complication patterns
COMPLICATION_PATTERNS = [
    r"(\w[\w\s]+?)\s+(?:is\s+a\s+)?complication\s+of\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+may\s+(?:result\s+)?(?:in|from)\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+can\s+lead\s+to\s+([^.;,]+)",
    r"(\w[\w\s]+?)\s+may\s+progress\s+to\s+([^.;,]+)",
    r"untreated\s+([^.;,]+?)\s+(?:can|may)\s+(?:cause|lead to|result in)\s+([^.;,]+)",
    r"([^.;,]+?)\s+complicated\s+by\s+([^.;,]+)",
]

# Progression patterns (for temporal_follows as well)
PROGRESSION_PATTERNS = [
    r"([^.;,]+?)\s+progresses?\s+to\s+([^.;,]+)",
    r"([^.;,]+?)\s+can\s+develop\s+into\s+([^.;,]+)",
    r"([^.;,]+?)\s+may\s+evolve\s+into\s+([^.;,]+)",
]


@dataclass
class ComplicationEdge:
    """Represents a complication relationship."""
    source: str  # Source disease ID (the complication)
    target: str  # Target disease ID (the primary disease)
    relationship_type: str = "complicates"
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


def load_diseases() -> Dict[str, Dict]:
    """Load diseases and create name->entity map."""
    file_path = PHASE2_DIR / "diseases.json"

    if not file_path.exists():
        print(f"❌ Error: {file_path} not found")
        return {}

    with open(file_path, encoding="utf-8") as f:
        entities = json.load(f)

    # Create name -> entity map
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


def find_disease_by_mention(mention: str, diseases: Dict[str, Dict]) -> str:
    """Find disease ID by mention text."""
    normalized = normalize_entity_mention(mention)

    # Exact match
    if normalized in diseases:
        return diseases[normalized].get("entity_id", "")

    # Partial match
    for disease_name, disease_data in diseases.items():
        if normalized in disease_name or disease_name in normalized:
            return disease_data.get("entity_id", "")

    return ""


def extract_complications_from_text(text: str, chapter: int, section: str, diseases: Dict) -> List[ComplicationEdge]:
    """Extract complication relationships from text."""
    edges = []

    # Check if this is a complications section
    is_complication_section = "complication" in section.lower() if section else False

    # Extract from patterns
    all_patterns = COMPLICATION_PATTERNS + PROGRESSION_PATTERNS

    for pattern in all_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            # Determine source and target based on pattern
            if "complication of" in match.group(0).lower():
                complication_mention = match.group(1).strip()
                disease_mention = match.group(2).strip()
            elif "untreated" in match.group(0).lower():
                disease_mention = match.group(1).strip()
                complication_mention = match.group(2).strip()
            elif "complicated by" in match.group(0).lower():
                disease_mention = match.group(1).strip()
                complication_mention = match.group(2).strip()
            else:
                disease_mention = match.group(1).strip()
                complication_mention = match.group(2).strip()

            # Find disease IDs
            disease_id = find_disease_by_mention(disease_mention, diseases)
            complication_id = find_disease_by_mention(complication_mention, diseases)

            if disease_id and complication_id and disease_id != complication_id:
                # Determine relationship type
                rel_type = "complicates"
                if "progress" in match.group(0).lower() or "evolve" in match.group(0).lower():
                    rel_type = "temporal_follows"

                edge = ComplicationEdge(
                    source=complication_id,  # The complication
                    target=disease_id,  # The disease it complicates
                    relationship_type=rel_type,
                    confidence=0.9 if is_complication_section else 0.7,
                    context=match.group(0),
                    chapter=chapter
                )
                edges.append(edge)

    return edges


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract complication relationships (baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 3 Compensation: Complication Relationships (Baseline)")
    print("=" * 80)
    print("Relationship types: complicates, temporal_follows")
    print("=" * 80)

    # Load data
    print("\n[1/3] Loading data...")
    diseases = load_diseases()
    text_blocks = load_text_blocks()

    print(f"  ✓ Diseases: {len(diseases)}")
    print(f"  ✓ Text blocks: {len(text_blocks)}")

    # Extract complications
    print("\n[2/3] Extracting complication relationships...")
    all_edges = []

    for block in text_blocks:
        text = block.get("text", "")
        chapter = block.get("chapter_number", 0)
        section = block.get("section_title", "")

        if not text or len(text) < 50:
            continue

        edges = extract_complications_from_text(text, chapter, section, diseases)
        all_edges.extend(edges)

    # Separate by type
    complicates_edges = [e for e in all_edges if e.relationship_type == "complicates"]
    temporal_edges = [e for e in all_edges if e.relationship_type == "temporal_follows"]

    print(f"  ✓ complicates: {len(complicates_edges)}")
    print(f"  ✓ temporal_follows: {len(temporal_edges)}")

    if args.dry_run:
        print("\n[DRY RUN] Sample edges:")
        if complicates_edges:
            print(f"\ncomplicates: {complicates_edges[0].to_dict()}")
        if temporal_edges:
            print(f"\ntemporal_follows: {temporal_edges[0].to_dict()}")
        return

    # Save edges
    print("\n[3/3] Saving edges...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_DIR / "complicates_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in complicates_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved complicates_edges.json ({len(complicates_edges)} edges)")

    with open(OUTPUT_DIR / "temporal_follows_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in temporal_edges], f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved temporal_follows_edges.json ({len(temporal_edges)} edges)")

    # Generate report
    report = {
        "extraction_method": "baseline_pattern_matching",
        "total_edges": len(all_edges),
        "by_type": {
            "complicates": len(complicates_edges),
            "temporal_follows": len(temporal_edges)
        },
        "patterns_used": len(COMPLICATION_PATTERNS) + len(PROGRESSION_PATTERNS)
    }

    with open(OUTPUT_DIR / "phase3_complications_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved phase3_complications_report.json")

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Edges: {report['total_edges']}")
    for edge_type, count in report['by_type'].items():
        print(f"  • {edge_type}: {count}")
    print("=" * 80)


if __name__ == "__main__":
    main()
