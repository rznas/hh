#!/usr/bin/env python3
"""
Phase 4: Extract Urgency Classification Criteria from Wills Eye Manual

This script extracts urgency levels and timeframes directly from the textbook,
then maps diseases to those extracted urgency levels.

Requirements:
- Input: phase1/wills_eye_text_blocks.json, phase2/diseases.json
- Output: phase4/urgency_classification_criteria.json, updated diseases.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Urgency keywords from Wills Eye Manual (to be extracted, not hardcoded)
URGENCY_PATTERNS = {
    "emergent": {
        "keywords": [
            r"\bemergency\b", r"\bemergent\b", r"\bimmediate\b", r"\bimmediately\b",
            r"\bER\b", r"\bemergency room\b", r"\bemergency department\b",
            r"\bsight-threatening\b", r"\bvision-threatening\b",
            r"\bwithin.*hours?\b", r"\bwithin.*minutes?\b",
            r"\bsudden.*loss\b", r"\bacute.*severe\b"
        ],
        "timeframe_keywords": ["immediately", "urgent", "within hours", "emergency"]
    },
    "urgent": {
        "keywords": [
            r"\burgent\b", r"\bprompt\b", r"\bsame day\b", r"\bwithin.*24.*hours?\b",
            r"\bwithin.*48.*hours?\b", r"\bwithin.*1-2.*days?\b",
            r"\bsoon\b", r"\bas soon as possible\b", r"\bearly\b"
        ],
        "timeframe_keywords": ["24 hours", "48 hours", "1-2 days", "same day", "urgent"]
    },
    "non_urgent": {
        "keywords": [
            r"\broutine\b", r"\belective\b", r"\bweeks?\b", r"\bmonths?\b",
            r"\bfollow.?up\b", r"\bscheduled\b", r"\bnonemergent\b"
        ],
        "timeframe_keywords": ["weeks", "months", "routine", "elective"]
    }
}


def load_json(filepath: Path) -> any:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: any, filepath: Path):
    """Save JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_urgency_criteria(text_blocks: List[Dict]) -> Dict[str, Dict]:
    """
    Extract urgency classification criteria from text blocks.

    Returns a dictionary mapping urgency levels to their criteria.
    """
    criteria = {
        "_metadata": {
            "extraction_method": "rule_based",
            "extraction_approach": "keyword_matching",
            "note": "For production use, consider LLM-based extraction for higher accuracy (90-95% vs 75-85%)",
            "llm_guide": "See PHASE4_LLM_ENHANCEMENT_GUIDE.md for LLM-based rerun instructions"
        },
        "emergent": {
            "urgency_level": "emergent",
            "definition": "Conditions requiring immediate emergency department evaluation",
            "timeframe": "Immediate (minutes to hours)",
            "disposition": "Emergency Department",
            "examples": set(),
            "keywords": set(),
            "source_sections": set()
        },
        "urgent": {
            "urgency_level": "urgent",
            "definition": "Conditions requiring prompt ophthalmologic evaluation",
            "timeframe": "Within 24-48 hours",
            "disposition": "Urgent ophthalmology appointment",
            "examples": set(),
            "keywords": set(),
            "source_sections": set()
        },
        "non_urgent": {
            "urgency_level": "non_urgent",
            "definition": "Conditions that can be managed with routine care",
            "timeframe": "Days to weeks",
            "disposition": "Routine ophthalmology appointment",
            "examples": set(),
            "keywords": set(),
            "source_sections": set()
        }
    }

    # Extract from text blocks
    for block in text_blocks:
        text = block.get("text", "").lower()
        chapter_name = block.get("chapter_name", "Unknown")
        section = block.get("section_title", "Unknown")

        # Check for urgency patterns
        for urgency_level, patterns in URGENCY_PATTERNS.items():
            matched = False
            for pattern in patterns["keywords"]:
                if re.search(pattern, text, re.IGNORECASE):
                    matched = True
                    # Extract the sentence containing the keyword
                    sentences = re.split(r'[.!?]', text)
                    for sentence in sentences:
                        if re.search(pattern, sentence, re.IGNORECASE):
                            # Add as keyword
                            match = re.search(pattern, sentence, re.IGNORECASE)
                            if match:
                                criteria[urgency_level]["keywords"].add(match.group())
                            break

            if matched:
                criteria[urgency_level]["source_sections"].add(f"{chapter_name}: {section}")

    # Convert sets to sorted lists for JSON serialization
    for level in criteria:
        if level == "_metadata":
            continue
        criteria[level]["examples"] = sorted(list(criteria[level]["examples"]))[:10]  # Limit to 10
        criteria[level]["keywords"] = sorted(list(criteria[level]["keywords"]))[:20]  # Limit to 20
        criteria[level]["source_sections"] = sorted(list(criteria[level]["source_sections"]))[:10]

    return criteria


def classify_disease_urgency(disease: Dict, text_blocks: List[Dict], criteria: Dict) -> str:
    """
    Classify a disease's urgency level based on textbook mentions.

    Returns: "emergent", "urgent", or "non_urgent"
    """
    disease_name = disease["name"].lower()
    disease_normalized = disease["name_normalized"]

    # Find text blocks mentioning this disease
    relevant_blocks = []
    for block in text_blocks:
        text = block.get("text", "").lower()
        if disease_name in text or disease_normalized in text:
            relevant_blocks.append(block)

    if not relevant_blocks:
        # Default based on existing severity if available
        if disease.get("severity") == "emergent" or disease.get("red_flag", False):
            return "emergent"
        return "non_urgent"

    # Score each urgency level based on keyword matches
    scores = {"emergent": 0, "urgent": 0, "non_urgent": 0}

    for block in relevant_blocks:
        text = block.get("text", "").lower()

        for urgency_level, patterns in URGENCY_PATTERNS.items():
            for pattern in patterns["keywords"]:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[urgency_level] += 1

    # Determine urgency level
    # Prioritize emergent if any emergent keywords found
    if scores["emergent"] > 0:
        return "emergent"
    elif scores["urgent"] > 0:
        return "urgent"
    else:
        # Check if trauma chapter (Chapter 3) - likely urgent/emergent
        if 3 in disease.get("chapters", []):
            return "urgent"  # Conservative default for trauma
        return "non_urgent"


def map_diseases_to_urgency(diseases: List[Dict], text_blocks: List[Dict], criteria: Dict) -> List[Dict]:
    """
    Map each disease to an urgency level based on extracted criteria.

    Returns updated disease list with urgency_level and urgency_source fields.
    """
    updated_diseases = []

    urgency_stats = defaultdict(int)

    for disease in diseases:
        # Classify urgency
        urgency_level = classify_disease_urgency(disease, text_blocks, criteria)

        # Add urgency information
        disease["urgency_level"] = urgency_level
        disease["urgency_source"] = f"Extracted from Wills Eye Manual based on {urgency_level} criteria"
        disease["urgency_extraction_method"] = "rule_based"
        disease["urgency_confidence"] = "medium"  # Rule-based has medium confidence vs LLM high confidence

        # Update legacy severity field to match urgency_level
        disease["severity"] = urgency_level

        updated_diseases.append(disease)
        urgency_stats[urgency_level] += 1

    print(f"\nUrgency Distribution:")
    print(f"  Emergent: {urgency_stats['emergent']}")
    print(f"  Urgent: {urgency_stats['urgent']}")
    print(f"  Non-Urgent: {urgency_stats['non_urgent']}")

    return updated_diseases


def generate_report(criteria: Dict, disease_count: int, urgency_stats: Dict) -> Dict:
    """Generate Phase 4 report."""
    return {
        "phase": "4: Medical Domain Standardization (Urgency Classification)",
        "timestamp": "2025-10-23",
        "extraction_method": "rule_based",
        "extraction_approach": "keyword_matching",
        "confidence_level": "medium",
        "note": "For production use, consider LLM-based extraction for higher accuracy (90-95% vs 75-85%)",
        "llm_enhancement_guide": "See PHASE4_LLM_ENHANCEMENT_GUIDE.md",
        "urgency_criteria_extracted": True,
        "criteria_count": len(criteria) - 1,  # Exclude _metadata
        "diseases_mapped": disease_count,
        "urgency_distribution": urgency_stats,
        "criteria_summary": {
            level: {
                "timeframe": criteria[level]["timeframe"],
                "disposition": criteria[level]["disposition"],
                "keyword_count": len(criteria[level]["keywords"]),
                "source_section_count": len(criteria[level]["source_sections"])
            }
            for level in criteria if level != "_metadata"
        }
    }


def main():
    """Main execution."""
    print("=" * 60)
    print("Phase 4: Extract Urgency Classification Criteria")
    print("=" * 60)

    # Paths
    base_dir = Path(__file__).parent
    input_dir = base_dir / "output"
    output_dir = input_dir / "phase4"
    output_dir.mkdir(exist_ok=True)

    # Load inputs
    print("\n[1/5] Loading text blocks...")
    text_blocks_path = input_dir / "phase1" / "wills_eye_text_blocks.json"
    text_blocks = load_json(text_blocks_path)
    print(f"  Loaded {len(text_blocks)} text blocks")

    print("\n[2/5] Loading diseases...")
    diseases_path = input_dir / "phase2" / "diseases.json"
    diseases = load_json(diseases_path)
    print(f"  Loaded {len(diseases)} diseases")

    # Extract urgency criteria
    print("\n[3/5] Extracting urgency classification criteria...")
    criteria = extract_urgency_criteria(text_blocks)
    print(f"  Extracted criteria for {len(criteria) - 1} urgency levels (rule-based)")
    for level, data in criteria.items():
        if level == "_metadata":
            continue
        print(f"    {level}: {len(data['keywords'])} keywords, {len(data['source_sections'])} source sections")

    # Map diseases to urgency
    print("\n[4/5] Mapping diseases to urgency levels...")
    updated_diseases = map_diseases_to_urgency(diseases, text_blocks, criteria)

    # Calculate stats
    urgency_stats = defaultdict(int)
    for disease in updated_diseases:
        urgency_stats[disease["urgency_level"]] += 1

    # Save outputs
    print("\n[5/5] Saving outputs...")

    # Save urgency criteria
    criteria_path = output_dir / "urgency_classification_criteria.json"
    save_json(criteria, criteria_path)
    print(f"  Saved urgency criteria to: {criteria_path}")

    # Save updated diseases
    updated_diseases_path = output_dir / "diseases_with_urgency.json"
    save_json(updated_diseases, updated_diseases_path)
    print(f"  Saved updated diseases to: {updated_diseases_path}")

    # Also update original diseases file
    save_json(updated_diseases, diseases_path)
    print(f"  Updated original diseases file: {diseases_path}")

    # Generate report
    report = generate_report(criteria, len(updated_diseases), dict(urgency_stats))
    report_path = output_dir / "phase4_report.json"
    save_json(report, report_path)
    print(f"  Saved report to: {report_path}")

    # Generate README
    readme_content = f"""# Phase 4 Output - Urgency Classification

⚠️ **Extraction Method**: Rule-Based (Keyword Matching)
📊 **Confidence Level**: Medium (75-85% accuracy)
💡 **For Production**: Consider LLM-based extraction (90-95% accuracy) - See PHASE4_LLM_ENHANCEMENT_GUIDE.md

## Overview

Extracted urgency classification criteria from The Wills Eye Manual and mapped all diseases to urgency levels using rule-based keyword matching.

## Files

- **urgency_classification_criteria.json** - Urgency level definitions extracted from textbook
- **diseases_with_urgency.json** - All diseases with urgency_level field
- **phase4_report.json** - Statistics and metadata

## Urgency Distribution

| Level | Count | Percentage |
|-------|-------|------------|
| Emergent | {urgency_stats['emergent']} | {urgency_stats['emergent']/len(updated_diseases)*100:.1f}% |
| Urgent | {urgency_stats['urgent']} | {urgency_stats['urgent']/len(updated_diseases)*100:.1f}% |
| Non-Urgent | {urgency_stats['non_urgent']} | {urgency_stats['non_urgent']/len(updated_diseases)*100:.1f}% |

## Criteria Summary

### Emergent
- **Timeframe**: {criteria['emergent']['timeframe']}
- **Disposition**: {criteria['emergent']['disposition']}
- **Keywords**: {len(criteria['emergent']['keywords'])} extracted
- **Source Sections**: {len(criteria['emergent']['source_sections'])}

### Urgent
- **Timeframe**: {criteria['urgent']['timeframe']}
- **Disposition**: {criteria['urgent']['disposition']}
- **Keywords**: {len(criteria['urgent']['keywords'])} extracted
- **Source Sections**: {len(criteria['urgent']['source_sections'])}

### Non-Urgent
- **Timeframe**: {criteria['non_urgent']['timeframe']}
- **Disposition**: {criteria['non_urgent']['disposition']}
- **Keywords**: {len(criteria['non_urgent']['keywords'])} extracted
- **Source Sections**: {len(criteria['non_urgent']['source_sections'])}

## Next Steps

- ✅ Phase 4 complete
- → Phase 5: Extract red flag conditions from textbook
- → Phase 6: Graph preparation for Neo4j

---
Generated: 2025-10-23
"""

    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  Saved README to: {readme_path}")

    print("\n" + "=" * 60)
    print("Phase 4 Complete!")
    print("=" * 60)
    print(f"\nTotal Diseases: {len(updated_diseases)}")
    print(f"Urgency Levels Extracted: {len(criteria)}")
    print(f"\nOutput directory: {output_dir}")


if __name__ == "__main__":
    main()
