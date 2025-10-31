#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract ETIOLOGY entities (Issue 1.3)

This script implements the baseline (non-LLM) approach for extracting etiology (causative factors)
from The Wills Eye Manual text blocks using pattern matching and section detection.

Approach:
- Detect "Etiology" sections in structured data
- Pattern matching for causal phrases ("caused by", "due to", "secondary to")
- Extract causative agents (infectious, traumatic, degenerative, etc.)

Input:
- Phase 1: wills_eye_text_blocks.json
- Phase 1: wills_eye_chapters_structured.json (for etiology sections)

Output:
- etiology.json (etiology entities with metadata)
- phase2_etiology_report.json (extraction statistics)

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_etiology.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "etiology.json"
REPORT_FILE = PHASE2_DIR / "phase2_etiology_report.json"

# Causal patterns to detect etiologies
CAUSAL_PATTERNS = [
    r"caused by\s+([^.;,]+)",
    r"due to\s+([^.;,]+)",
    r"secondary to\s+([^.;,]+)",
    r"etiology[:\s]+([^.;]+)",
    r"resulting from\s+([^.;,]+)",
    r"associated with\s+([^.;,]+)",
    r"following\s+([^.;,]+)",
    r"induced by\s+([^.;,]+)",
]

# Common etiology categories (for classification)
ETIOLOGY_CATEGORIES = {
    "infectious": ["bacteria", "virus", "fungal", "parasit", "infection", "microbial", "pathogen"],
    "traumatic": ["trauma", "injury", "blunt", "penetrating", "laceration", "contusion", "foreign body"],
    "autoimmune": ["autoimmune", "immune-mediated", "immunologic"],
    "degenerative": ["degeneration", "aging", "age-related", "senile"],
    "congenital": ["congenital", "hereditary", "genetic", "familial", "inherited"],
    "iatrogenic": ["post-operative", "surgical", "post-surgery", "medication", "drug-induced"],
    "inflammatory": ["inflammation", "inflammatory"],
    "neoplastic": ["tumor", "neoplasm", "cancer", "malignancy"],
    "vascular": ["vascular", "ischemic", "thrombosis", "occlusion", "hemorrhage"],
    "metabolic": ["metabolic", "diabetes", "thyroid"],
    "toxic": ["toxic", "chemical", "exposure"],
    "idiopathic": ["idiopathic", "unknown cause", "unclear etiology"]
}


@dataclass
class EtiologyEntity:
    """Represents an etiology entity."""
    entity_id: str
    name: str
    name_normalized: str
    type: str = "etiology"
    category: str = "unclassified"
    mentions_count: int = 0
    associated_diseases: List[str] = field(default_factory=list)
    chapters: List[int] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)
    extraction_method: str = "pattern_matching"

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "name_normalized": self.name_normalized,
            "type": self.type,
            "category": self.category,
            "mentions_count": self.mentions_count,
            "associated_diseases": sorted(list(set(self.associated_diseases)))[:10],
            "chapters": sorted(list(set(self.chapters))),
            "sections": sorted(list(set(self.sections))),
            "sample_contexts": self.contexts[:3],
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


def load_diseases() -> List[Dict]:
    """Load existing disease entities to associate etiologies."""
    diseases_file = PHASE2_DIR / "diseases.json"
    if diseases_file.exists():
        with open(diseases_file, encoding="utf-8") as f:
            return json.load(f)
    return []


def normalize_etiology_name(name: str) -> str:
    """Normalize etiology name."""
    normalized = name.lower().strip()
    # Remove articles
    normalized = re.sub(r'^(a|an|the)\s+', '', normalized)
    # Clean whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def classify_etiology(etiology_text: str) -> str:
    """Classify etiology into category."""
    text_lower = etiology_text.lower()

    for category, keywords in ETIOLOGY_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return "unclassified"


def extract_etiologies_from_text(text: str, chapter: int, section: str, disease_name: str = "") -> Dict[str, Dict]:
    """
    Extract etiologies from text using causal patterns.
    Returns dict: {normalized_name: {name, category, mentions, contexts, etc.}}
    """
    found_etiologies = {}

    # Check if this is an "Etiology" section
    is_etiology_section = "etiology" in section.lower() if section else False

    # If it's an etiology section, extract more aggressively
    if is_etiology_section:
        # Split by common delimiters
        potential_causes = re.split(r'[;,]\s*(?=[A-Z])', text)

        for cause in potential_causes[:10]:  # Limit to avoid noise
            cause = cause.strip()
            if 5 < len(cause) < 150:  # Reasonable length
                normalized = normalize_etiology_name(cause)

                if normalized not in found_etiologies:
                    found_etiologies[normalized] = {
                        "name": cause[:100],  # Truncate long names
                        "category": classify_etiology(cause),
                        "mentions": 0,
                        "associated_diseases": [],
                        "chapters": set(),
                        "sections": set(),
                        "contexts": []
                    }

                found_etiologies[normalized]["mentions"] += 1
                found_etiologies[normalized]["chapters"].add(chapter)
                found_etiologies[normalized]["sections"].add(section)
                if disease_name:
                    found_etiologies[normalized]["associated_diseases"].append(disease_name)
                found_etiologies[normalized]["contexts"].append(f"[Etiology section] {cause[:100]}")

    # Pattern-based extraction
    for pattern in CAUSAL_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            cause = match.group(1).strip()

            # Clean up the extracted cause
            cause = re.sub(r'\s+', ' ', cause)
            if len(cause) < 5 or len(cause) > 150:
                continue

            # Remove trailing conjunctions/prepositions
            cause = re.sub(r'\s+(and|or|with|in|at|on)$', '', cause, flags=re.IGNORECASE)

            normalized = normalize_etiology_name(cause)

            if normalized not in found_etiologies:
                found_etiologies[normalized] = {
                    "name": cause.title(),
                    "category": classify_etiology(cause),
                    "mentions": 0,
                    "associated_diseases": [],
                    "chapters": set(),
                    "sections": set(),
                    "contexts": []
                }

            found_etiologies[normalized]["mentions"] += 1
            found_etiologies[normalized]["chapters"].add(chapter)
            found_etiologies[normalized]["sections"].add(section)
            if disease_name:
                found_etiologies[normalized]["associated_diseases"].append(disease_name)

            # Extract context
            if len(found_etiologies[normalized]["contexts"]) < 5:
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 60)
                context = text[start:end].replace("\n", " ").strip()
                found_etiologies[normalized]["contexts"].append(f"...{context}...")

    return found_etiologies


def create_entity_id(index: int) -> str:
    """Generate etiology entity ID."""
    return f"etiology_{index:03d}"


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract ETIOLOGY entities (baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: ETIOLOGY Entity Extraction (Baseline)")
    print("=" * 80)
    print(f"Method: Pattern matching + section detection")
    print(f"Patterns: {len(CAUSAL_PATTERNS)} causal patterns")
    print(f"Categories: {len(ETIOLOGY_CATEGORIES)} etiology types")
    print("=" * 80)

    # Load data
    print("\n[1/4] Loading data...")
    text_blocks = load_text_blocks()
    diseases = load_diseases()
    print(f"  ✓ Loaded {len(text_blocks)} text blocks")
    print(f"  ✓ Loaded {len(diseases)} diseases (for association)")

    # Create disease name map for matching
    disease_names = {d.get("name", "").lower(): d.get("name", "") for d in diseases}

    # Extract etiologies
    print("\n[2/4] Extracting etiology entities...")
    all_etiologies = defaultdict(lambda: {
        "name": "",
        "category": "unclassified",
        "mentions": 0,
        "associated_diseases": [],
        "chapters": set(),
        "sections": set(),
        "contexts": []
    })

    for block in text_blocks:
        text = block.get("text", "")
        chapter = block.get("chapter_number", 0)
        section = block.get("section_title", "")

        if not text or len(text.strip()) < 30:
            continue

        # Try to determine associated disease from context
        disease_name = ""
        for disease_lower, disease_proper in disease_names.items():
            if disease_lower in text.lower()[:200]:  # Check first 200 chars
                disease_name = disease_proper
                break

        block_etiologies = extract_etiologies_from_text(text, chapter, section, disease_name)

        # Merge findings
        for normalized, data in block_etiologies.items():
            if not all_etiologies[normalized]["name"]:
                all_etiologies[normalized]["name"] = data["name"]
            if all_etiologies[normalized]["category"] == "unclassified":
                all_etiologies[normalized]["category"] = data["category"]
            all_etiologies[normalized]["mentions"] += data["mentions"]
            all_etiologies[normalized]["associated_diseases"].extend(data["associated_diseases"])
            all_etiologies[normalized]["chapters"].update(data["chapters"])
            all_etiologies[normalized]["sections"].update(data["sections"])
            all_etiologies[normalized]["contexts"].extend(data["contexts"])

    print(f"  ✓ Found {len(all_etiologies)} unique etiology entities")

    # Create entity objects
    print("\n[3/4] Creating entity objects...")
    entities = []
    for idx, (normalized, data) in enumerate(sorted(all_etiologies.items()), 1):
        entity = EtiologyEntity(
            entity_id=create_entity_id(idx),
            name=data["name"],
            name_normalized=normalized,
            category=data["category"],
            mentions_count=data["mentions"],
            associated_diseases=data["associated_diseases"],
            chapters=list(data["chapters"]),
            sections=list(data["sections"]),
            contexts=data["contexts"][:3]
        )
        entities.append(entity)

    # Sort by mention count
    entities.sort(key=lambda e: e.mentions_count, reverse=True)

    # Re-assign IDs
    for idx, entity in enumerate(entities, 1):
        entity.entity_id = create_entity_id(idx)

    # Show stats
    category_counts = defaultdict(int)
    for entity in entities:
        category_counts[entity.category] += 1

    print(f"  ✓ Created {len(entities)} entities")
    print(f"\n  By category:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    • {category}: {count}")

    if args.dry_run:
        print("\n[DRY RUN] Would save to:", OUTPUT_FILE)
        print("\nSample entities:")
        for entity in entities[:3]:
            print(json.dumps(entity.to_dict(), indent=2))
        return

    # Save entities
    print("\n[4/4] Saving entities...")
    entities_json = [e.to_dict() for e in entities]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(entities_json, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(entities)} entities to {OUTPUT_FILE}")

    # Generate report
    report = {
        "extraction_method": "baseline_pattern_matching",
        "total_entities": len(entities),
        "total_mentions": sum(e.mentions_count for e in entities),
        "by_category": dict(category_counts),
        "patterns_used": len(CAUSAL_PATTERNS),
        "top_entities": [
            {
                "name": e.name,
                "category": e.category,
                "mentions": e.mentions_count,
                "associated_diseases_count": len(set(e.associated_diseases))
            }
            for e in entities[:15]
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
    print(f"Most common category: {max(category_counts, key=category_counts.get)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
