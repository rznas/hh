#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract RISK_FACTOR entities (Issue 1.4)

This script implements the baseline (non-LLM) approach for extracting risk factors
from The Wills Eye Manual text blocks using pattern matching.

Approach:
- Pattern matching for risk phrases ("risk factor", "increases risk", "predispose")
- Section detection ("Risk Factors", "Predisposing Factors")
- Common risk factor categories (age, comorbidity, behavior, etc.)

Input:
- Phase 1: wills_eye_text_blocks.json

Output:
- risk_factors.json (risk factor entities with metadata)
- phase2_risk_factors_report.json (extraction statistics)

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_risk_factors.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_compensate_risk_factors.py --dry-run
"""

import json
import re
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from dataclasses import dataclass, field

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
OUTPUT_FILE = PHASE2_DIR / "risk_factors.json"
REPORT_FILE = PHASE2_DIR / "phase2_risk_factors_report.json"

# Risk factor patterns
RISK_PATTERNS = [
    r"risk factor[s]?[:\s]+([^.;]+)",
    r"increased risk[:\s]+([^.;]+)",
    r"predispos(?:ing|ed)[:\s]+([^.;]+)",
    r"associated with\s+([^.;,]+)\s+(?:in patients with|with)",
    r"more common in\s+([^.;]+)",
    r"(?:higher|greater) risk in\s+([^.;]+)",
]

# Common risk factor categories
RISK_CATEGORIES = {
    "demographic": ["age", "gender", "race", "ethnicity", "male", "female", "elderly", "pediatric"],
    "comorbidity": ["diabetes", "hypertension", "immunocompromised", "systemic disease", "autoimmune"],
    "behavioral": ["smoking", "alcohol", "drug use", "contact lens", "poor hygiene"],
    "environmental": ["exposure", "climate", "allergen", "pollution", "occupational"],
    "anatomical": ["anatomy", "structural", "congenital anomaly"],
    "iatrogenic": ["surgery", "post-operative", "medication", "treatment"],
    "genetic": ["family history", "genetic", "hereditary", "familial"],
    "infectious": ["prior infection", "chronic infection", "immunosuppression"]
}

# Predefined common ocular risk factors
COMMON_RISK_FACTORS = [
    "advanced age", "diabetes mellitus", "hypertension",
    "contact lens wear", "immunocompromised state",
    "previous ocular surgery", "trauma", "family history",
    "smoking", "prolonged steroid use", "autoimmune disease"
]


@dataclass
class RiskFactorEntity:
    """Represents a risk factor entity."""
    entity_id: str
    name: str
    name_normalized: str
    type: str = "risk_factor"
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
    """Load existing disease entities to associate risk factors."""
    diseases_file = PHASE2_DIR / "diseases.json"
    if diseases_file.exists():
        with open(diseases_file, encoding="utf-8") as f:
            return json.load(f)
    return []


def normalize_risk_factor_name(name: str) -> str:
    """Normalize risk factor name."""
    normalized = name.lower().strip()
    # Remove articles
    normalized = re.sub(r'^(a|an|the)\s+', '', normalized)
    # Clean whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def classify_risk_factor(risk_text: str) -> str:
    """Classify risk factor into category."""
    text_lower = risk_text.lower()

    for category, keywords in RISK_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    return "unclassified"


def extract_risk_factors_from_text(text: str, chapter: int, section: str, disease_name: str = "") -> Dict[str, Dict]:
    """
    Extract risk factors from text using patterns.
    Returns dict: {normalized_name: {name, category, mentions, contexts, etc.}}
    """
    found_risks = {}

    # Check if this is a risk factor section
    is_risk_section = any(keyword in section.lower() for keyword in ["risk", "predispos"]) if section else False

    # If it's a risk factors section, extract more aggressively
    if is_risk_section:
        # Split by common delimiters
        potential_risks = re.split(r'[;,]\s*(?=[A-Z])', text)

        for risk in potential_risks[:15]:  # Limit to avoid noise
            risk = risk.strip()
            if 5 < len(risk) < 100:
                normalized = normalize_risk_factor_name(risk)

                if normalized not in found_risks:
                    found_risks[normalized] = {
                        "name": risk[:80],
                        "category": classify_risk_factor(risk),
                        "mentions": 0,
                        "associated_diseases": [],
                        "chapters": set(),
                        "sections": set(),
                        "contexts": []
                    }

                found_risks[normalized]["mentions"] += 1
                found_risks[normalized]["chapters"].add(chapter)
                found_risks[normalized]["sections"].add(section)
                if disease_name:
                    found_risks[normalized]["associated_diseases"].append(disease_name)
                found_risks[normalized]["contexts"].append(f"[Risk factors section] {risk[:80]}")

    # Pattern-based extraction
    for pattern in RISK_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            risk = match.group(1).strip()

            # Clean up
            risk = re.sub(r'\s+', ' ', risk)
            if len(risk) < 5 or len(risk) > 100:
                continue

            # Remove trailing conjunctions
            risk = re.sub(r'\s+(and|or|with|in|at|such as)$', '', risk, flags=re.IGNORECASE)

            normalized = normalize_risk_factor_name(risk)

            if normalized not in found_risks:
                found_risks[normalized] = {
                    "name": risk.title(),
                    "category": classify_risk_factor(risk),
                    "mentions": 0,
                    "associated_diseases": [],
                    "chapters": set(),
                    "sections": set(),
                    "contexts": []
                }

            found_risks[normalized]["mentions"] += 1
            found_risks[normalized]["chapters"].add(chapter)
            found_risks[normalized]["sections"].add(section)
            if disease_name:
                found_risks[normalized]["associated_diseases"].append(disease_name)

            # Extract context
            if len(found_risks[normalized]["contexts"]) < 5:
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 60)
                context = text[start:end].replace("\n", " ").strip()
                found_risks[normalized]["contexts"].append(f"...{context}...")

    # Check for common predefined risk factors
    for common_risk in COMMON_RISK_FACTORS:
        if common_risk.lower() in text.lower():
            normalized = normalize_risk_factor_name(common_risk)

            if normalized not in found_risks:
                found_risks[normalized] = {
                    "name": common_risk.title(),
                    "category": classify_risk_factor(common_risk),
                    "mentions": 0,
                    "associated_diseases": [],
                    "chapters": set(),
                    "sections": set(),
                    "contexts": []
                }

            found_risks[normalized]["mentions"] += 1
            found_risks[normalized]["chapters"].add(chapter)
            found_risks[normalized]["sections"].add(section)
            if disease_name:
                found_risks[normalized]["associated_diseases"].append(disease_name)

    return found_risks


def create_entity_id(index: int) -> str:
    """Generate risk factor entity ID."""
    return f"risk_factor_{index:03d}"


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract RISK_FACTOR entities (baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: RISK_FACTOR Entity Extraction (Baseline)")
    print("=" * 80)
    print(f"Method: Pattern matching + section detection")
    print(f"Patterns: {len(RISK_PATTERNS)} risk patterns")
    print(f"Common risk factors: {len(COMMON_RISK_FACTORS)}")
    print("=" * 80)

    # Load data
    print("\n[1/4] Loading data...")
    text_blocks = load_text_blocks()
    diseases = load_diseases()
    print(f"  ✓ Loaded {len(text_blocks)} text blocks")
    print(f"  ✓ Loaded {len(diseases)} diseases (for association)")

    # Create disease name map
    disease_names = {d.get("name", "").lower(): d.get("name", "") for d in diseases}

    # Extract risk factors
    print("\n[2/4] Extracting risk factor entities...")
    all_risks = defaultdict(lambda: {
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

        # Try to determine associated disease
        disease_name = ""
        for disease_lower, disease_proper in disease_names.items():
            if disease_lower in text.lower()[:200]:
                disease_name = disease_proper
                break

        block_risks = extract_risk_factors_from_text(text, chapter, section, disease_name)

        # Merge findings
        for normalized, data in block_risks.items():
            if not all_risks[normalized]["name"]:
                all_risks[normalized]["name"] = data["name"]
            if all_risks[normalized]["category"] == "unclassified":
                all_risks[normalized]["category"] = data["category"]
            all_risks[normalized]["mentions"] += data["mentions"]
            all_risks[normalized]["associated_diseases"].extend(data["associated_diseases"])
            all_risks[normalized]["chapters"].update(data["chapters"])
            all_risks[normalized]["sections"].update(data["sections"])
            all_risks[normalized]["contexts"].extend(data["contexts"])

    print(f"  ✓ Found {len(all_risks)} unique risk factor entities")

    # Create entity objects
    print("\n[3/4] Creating entity objects...")
    entities = []
    for idx, (normalized, data) in enumerate(sorted(all_risks.items()), 1):
        entity = RiskFactorEntity(
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
        "patterns_used": len(RISK_PATTERNS),
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
    print(f"Most common category: {max(category_counts, key=category_counts.get) if category_counts else 'N/A'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
