#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract ANATOMY entities (Issue 1.2)

This script implements the baseline (non-LLM) approach for extracting anatomical entities
from The Wills Eye Manual text blocks using pattern matching and predefined anatomical terms.

Approach:
- Uses predefined ANATOMICAL_TERMS from config.py
- Pattern matching in text blocks
- Context-aware extraction (checks for anatomical references)
- Deduplication and normalization

Input:
- Phase 1: wills_eye_text_blocks.json

Output:
- anatomy.json (anatomical entities with metadata)
- phase2_anatomy_report.json (extraction statistics)

Usage:
    # Run baseline extraction
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy.py

    # Dry run (preview without saving)
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_anatomy.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "anatomy.json"
REPORT_FILE = PHASE2_DIR / "phase2_anatomy_report.json"

# Import from config (inline for portability)
ANATOMICAL_TERMS = [
    "cornea", "conjunctiva", "sclera", "iris", "pupil",
    "lens", "retina", "macula", "optic nerve", "vitreous",
    "anterior chamber", "posterior chamber", "eyelid",
    "orbit", "lacrimal gland", "tear duct",
    # Extended terms based on ocular anatomy
    "choroid", "ciliary body", "trabecular meshwork",
    "limbus", "descemet's membrane", "bowman's layer",
    "endothelium", "epithelium", "stroma",
    "fovea", "optic disc", "optic cup",
    "extraocular muscles", "rectus muscle", "oblique muscle",
    "lacrimal sac", "nasolacrimal duct", "meibomian gland",
    "tarsal plate", "canthal tendon", "orbital septum",
    "zonules", "capsule", "equator"
]


@dataclass
class AnatomyEntity:
    """Represents an anatomical entity."""
    entity_id: str
    name: str
    name_normalized: str
    type: str = "anatomy"
    mentions_count: int = 0
    chapters: List[int] = None
    sections: List[str] = None
    contexts: List[str] = None
    extraction_method: str = "pattern_matching"

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "type": self.type,
            "mentions_count": self.mentions_count,
            "chapters": sorted(list(set(self.chapters))) if self.chapters else [],
            "sections": sorted(list(set(self.sections))) if self.sections else [],
            "sample_contexts": self.contexts[:3] if self.contexts else [],
            "metadata": {
                "extraction_method": self.extraction_method,
                "source": "wills_eye_manual"
            }
        }


def load_text_blocks() -> List[Dict]:
    """Load Phase 1 text blocks."""
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else data.get("text_blocks", [])


def normalize_anatomy_name(name: str) -> str:
    """Normalize anatomical term for consistency."""
    # Remove possessives, standardize spacing
    normalized = name.lower().strip()
    normalized = re.sub(r"'s\b", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def extract_anatomy_from_text(text: str, chapter: int, section: str) -> Dict[str, Dict]:
    """
    Extract anatomical entities from text using pattern matching.
    Returns dict: {normalized_name: {mentions, contexts, chapters, sections}}
    """
    text_lower = text.lower()
    found_anatomy = {}

    for anatomy_term in ANATOMICAL_TERMS:
        # Create pattern for whole word matching (with plural support)
        term_pattern = re.escape(anatomy_term.lower())
        # Allow plural forms
        pattern = rf'\b{term_pattern}(?:s|es)?\b'

        matches = list(re.finditer(pattern, text_lower))

        if matches:
            normalized = normalize_anatomy_name(anatomy_term)

            if normalized not in found_anatomy:
                found_anatomy[normalized] = {
                    "name": anatomy_term.title(),
                    "mentions": 0,
                    "chapters": set(),
                    "sections": set(),
                    "contexts": []
                }

            # Count mentions
            found_anatomy[normalized]["mentions"] += len(matches)
            found_anatomy[normalized]["chapters"].add(chapter)
            if section:
                found_anatomy[normalized]["sections"].add(section)

            # Extract context (50 chars before and after first mention)
            if len(found_anatomy[normalized]["contexts"]) < 5:
                match = matches[0]
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].replace("\n", " ").strip()
                found_anatomy[normalized]["contexts"].append(f"...{context}...")

    return found_anatomy


def create_entity_id(index: int) -> str:
    """Generate anatomy entity ID."""
    return f"anatomy_{index:03d}"


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract ANATOMY entities (baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: ANATOMY Entity Extraction (Baseline)")
    print("=" * 80)
    print(f"Method: Pattern matching with predefined anatomical terms")
    print(f"Terms: {len(ANATOMICAL_TERMS)} anatomical structures")
    print("=" * 80)

    # Load text blocks
    print("\n[1/3] Loading Phase 1 text blocks...")
    text_blocks = load_text_blocks()
    print(f"  ✓ Loaded {len(text_blocks)} text blocks")

    # Extract anatomy entities
    print("\n[2/3] Extracting anatomy entities...")
    all_anatomy = defaultdict(lambda: {
        "name": "",
        "mentions": 0,
        "chapters": set(),
        "sections": set(),
        "contexts": []
    })

    for block in text_blocks:
        text = block.get("text", "")
        chapter = block.get("chapter_number", 0)
        section = block.get("section_title", "")

        if not text or len(text.strip()) < 20:
            continue

        block_anatomy = extract_anatomy_from_text(text, chapter, section)

        # Merge findings
        for normalized, data in block_anatomy.items():
            if not all_anatomy[normalized]["name"]:
                all_anatomy[normalized]["name"] = data["name"]
            all_anatomy[normalized]["mentions"] += data["mentions"]
            all_anatomy[normalized]["chapters"].update(data["chapters"])
            all_anatomy[normalized]["sections"].update(data["sections"])
            all_anatomy[normalized]["contexts"].extend(data["contexts"])

    print(f"  ✓ Found {len(all_anatomy)} unique anatomical entities")

    # Create entity objects
    entities = []
    for idx, (normalized, data) in enumerate(sorted(all_anatomy.items()), 1):
        entity = AnatomyEntity(
            entity_id=create_entity_id(idx),
            name=data["name"],
            name_normalized=normalized,
            mentions_count=data["mentions"],
            chapters=list(data["chapters"]),
            sections=list(data["sections"]),
            contexts=data["contexts"][:3]  # Keep top 3 contexts
        )
        entities.append(entity)

    # Sort by mention count (most mentioned first)
    entities.sort(key=lambda e: e.mentions_count, reverse=True)

    # Re-assign IDs after sorting
    for idx, entity in enumerate(entities, 1):
        entity.entity_id = create_entity_id(idx)

    print(f"\n  Top 5 most mentioned:")
    for entity in entities[:5]:
        print(f"    • {entity.name}: {entity.mentions_count} mentions")

    if args.dry_run:
        print("\n[DRY RUN] Would save to:", OUTPUT_FILE)
        print("\nSample entities:")
        for entity in entities[:3]:
            print(json.dumps(entity.to_dict(), indent=2))
        return

    # Save entities
    print("\n[3/3] Saving entities...")
    entities_json = [e.to_dict() for e in entities]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entities_json, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(entities)} entities to {OUTPUT_FILE}")

    # Generate report
    chapter_distribution = defaultdict(int)
    for entity in entities:
        for chapter in entity.chapters:
            chapter_distribution[chapter] += 1

    report = {
        "extraction_method": "baseline_pattern_matching",
        "total_entities": len(entities),
        "total_mentions": sum(e.mentions_count for e in entities),
        "avg_mentions_per_entity": round(sum(e.mentions_count for e in entities) / len(entities), 2) if entities else 0,
        "predefined_terms_used": len(ANATOMICAL_TERMS),
        "chapter_distribution": dict(sorted(chapter_distribution.items())),
        "top_entities": [
            {
                "name": e.name,
                "mentions": e.mentions_count,
                "chapters": len(e.chapters)
            }
            for e in entities[:10]
        ]
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved report to {REPORT_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Entities: {len(entities)}")
    print(f"Total Mentions: {sum(e.mentions_count for e in entities):,}")
    print(f"Chapters Covered: {len(chapter_distribution)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
