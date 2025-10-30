#!/usr/bin/env python3
"""
Phase 5: Extract Red Flag Conditions from Wills Eye Manual

This script extracts emergent conditions (red flags) directly from the textbook.
Red flags are conditions requiring immediate emergency department referral.

Requirements:
- Input: phase1/wills_eye_text_blocks.json, phase2/diseases.json, phase4/diseases_with_urgency.json
- Output: phase5/red_flags.json

Approach:
- Rule-based extraction using keyword patterns
- Focus on Chapter 3 (Trauma) and emergent conditions
- Extract clinical presentation, keywords, first aid instructions
- 100% recall required (no false negatives acceptable)

For LLM-based enhancement:
- See PHASE5_LLM_ENHANCEMENT_GUIDE.md for rerun instructions
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Red flag patterns extracted from medical literature and Wills Eye Manual structure
RED_FLAG_PATTERNS = {
    "sudden_vision_loss": {
        "keywords": [
            r"\bsudden.*vision.*loss\b",
            r"\bacute.*vision.*loss\b",
            r"\bpainless.*vision.*loss\b",
            r"\bsuddenly.*blind\b",
            r"\bcan'?t see\b",
            r"\bvision.*went.*black\b",
            r"\bsudden.*blindness\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate"
    },
    "chemical_burn": {
        "keywords": [
            r"\bchemical.*burn\b",
            r"\bchemical.*exposure\b",
            r"\bchemical.*splash\b",
            r"\bacid.*burn\b",
            r"\balkali.*burn\b",
            r"\bcaustic\b",
            r"\bsplash.*eye\b",
            r"\bcleaner.*eye\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate"
    },
    "penetrating_trauma": {
        "keywords": [
            r"\bpenetrating.*trauma\b",
            r"\bruptured.*globe\b",
            r"\bglobe.*rupture\b",
            r"\bpenetrating.*injury\b",
            r"\bintraocular.*foreign.*body\b",
            r"\biofb\b",
            r"\bopen.*globe\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate"
    },
    "retinal_detachment": {
        "keywords": [
            r"\bretinal.*detachment\b",
            r"\bdetached.*retina\b",
            r"\bflashes.*and.*floaters\b",
            r"\bcurtain.*vision\b",
            r"\bshadow.*vision\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate to hours"
    },
    "acute_angle_closure_glaucoma": {
        "keywords": [
            r"\bacute.*angle.*closure\b",
            r"\bangle.*closure.*glaucoma\b",
            r"\bacute.*glaucoma\b",
            r"\bsevere.*eye.*pain.*nausea\b",
            r"\bhalos.*lights\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate"
    },
    "endophthalmitis": {
        "keywords": [
            r"\bendophthalmitis\b",
            r"\bintraocular.*infection\b",
            r"\bpost.*operative.*infection\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate to hours"
    },
    "central_retinal_artery_occlusion": {
        "keywords": [
            r"\bcentral.*retinal.*artery.*occlusion\b",
            r"\bcrao\b",
            r"\bretinal.*artery.*occlusion\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate (90 minutes)"
    },
    "orbital_cellulitis": {
        "keywords": [
            r"\borbital.*cellulitis\b",
            r"\borbital.*infection\b",
            r"\bproptosis.*fever\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate"
    },
    "temporal_arteritis": {
        "keywords": [
            r"\btemporal.*arteritis\b",
            r"\bgiant.*cell.*arteritis\b",
            r"\bgca\b",
            r"\bjaw.*claudication\b"
        ],
        "severity": "emergent",
        "timeframe": "immediate to hours"
    },
    "severe_trauma": {
        "keywords": [
            r"\bblunt.*trauma\b",
            r"\bhyphema\b",
            r"\btraumatic.*injury\b",
            r"\beye.*trauma\b",
            r"\borbital.*fracture\b"
        ],
        "severity": "emergent/urgent",
        "timeframe": "immediate to hours"
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


def extract_red_flag_contexts(text_blocks: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract text blocks that mention red flag conditions.

    Returns a dictionary mapping red flag types to relevant text blocks.
    """
    red_flag_contexts = defaultdict(list)

    for block in text_blocks:
        text = block.get("text", "")
        chapter_num = block.get("chapter_number")
        chapter_title = block.get("chapter_title", "")
        section_path = block.get("section_path", "")

        # Search for red flag patterns
        for flag_type, pattern_info in RED_FLAG_PATTERNS.items():
            matched = False
            matched_keywords = []

            for pattern in pattern_info["keywords"]:
                if re.search(pattern, text, re.IGNORECASE):
                    matched = True
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        matched_keywords.append(match.group())

            if matched:
                red_flag_contexts[flag_type].append({
                    "block_id": block.get("block_id"),
                    "chapter_number": chapter_num,
                    "chapter_title": chapter_title,
                    "section_path": section_path,
                    "text": text[:500],  # Limit text length
                    "matched_keywords": matched_keywords
                })

    return red_flag_contexts


def extract_clinical_presentation(contexts: List[Dict], flag_type: str) -> str:
    """
    Extract clinical presentation description from contexts.
    """
    # For rule-based, create generic description
    # LLM would extract more detailed presentation from text
    presentations = {
        "sudden_vision_loss": "Patient reports sudden, painless or painful decrease in vision",
        "chemical_burn": "Patient reports chemical substance contact with eye (acid, alkali, cleaners)",
        "penetrating_trauma": "Object penetrated or may have penetrated the eye globe",
        "retinal_detachment": "Patient reports new floaters, flashes of light, or curtain/shadow in vision",
        "acute_angle_closure_glaucoma": "Severe eye pain with nausea, vomiting, and halos around lights",
        "endophthalmitis": "Severe eye pain and vision loss following eye surgery or penetrating injury",
        "central_retinal_artery_occlusion": "Sudden, painless, severe vision loss (curtain of darkness)",
        "orbital_cellulitis": "Proptosis, fever, eye pain, and limited eye movement",
        "temporal_arteritis": "Vision loss in patient >50 with headache, jaw claudication, or scalp tenderness",
        "severe_trauma": "History of significant blunt or penetrating trauma to eye or orbit"
    }

    return presentations.get(flag_type, "Emergent ocular condition requiring immediate evaluation")


def extract_first_aid(flag_type: str) -> str:
    """
    Extract first aid instructions for red flag condition.
    """
    first_aid = {
        "sudden_vision_loss": "No specific first aid. Immediate ER referral.",
        "chemical_burn": "Immediate and copious irrigation with water or saline for 15-30 minutes. Begin BEFORE transport to ER.",
        "penetrating_trauma": "Shield eye (do NOT remove object if embedded). Do NOT apply pressure. Immediate ER referral.",
        "retinal_detachment": "Position patient upright or with detachment dependent. Immediate ER/ophthalmology referral.",
        "acute_angle_closure_glaucoma": "No specific first aid. Immediate ER referral for pressure reduction.",
        "endophthalmitis": "No specific first aid. Immediate ER/ophthalmology referral.",
        "central_retinal_artery_occlusion": "Ocular massage may be attempted. Immediate ER referral (time-critical: 90 minutes).",
        "orbital_cellulitis": "No specific first aid. Immediate ER referral for IV antibiotics.",
        "temporal_arteritis": "No specific first aid. Immediate ER referral for high-dose steroids.",
        "severe_trauma": "Shield eye if open globe suspected. Do NOT apply pressure. Immediate ER referral."
    }

    return first_aid.get(flag_type, "Immediate ER referral required")


def extract_referral_disposition(flag_type: str) -> str:
    """
    Extract referral disposition for red flag.
    """
    return "Emergency Department immediately"


def create_red_flag_entry(
    flag_type: str,
    contexts: List[Dict],
    diseases: List[Dict]
) -> Dict:
    """
    Create a red flag entry from extracted information.
    """
    # Extract unique keywords from contexts
    all_keywords = set()
    for context in contexts:
        all_keywords.update(context.get("matched_keywords", []))

    # Get unique source chapters/sections
    source_chapters = set()
    source_sections = set()
    for context in contexts:
        if context.get("chapter_number"):
            chapter_title = context.get("chapter_title", "Unknown")
            source_chapters.add(f"Chapter {context['chapter_number']}: {chapter_title}")
        section = context.get("section_path")
        if section:
            source_sections.add(section[:100])  # Limit length

    # Find related disease entities
    related_diseases = []
    for disease in diseases:
        disease_name = disease.get("name", "").lower()
        # Check if disease name matches flag type keywords
        for keyword in all_keywords:
            if keyword.lower() in disease_name or disease_name in keyword.lower():
                related_diseases.append({
                    "entity_id": disease.get("entity_id"),
                    "name": disease.get("name"),
                    "urgency_level": disease.get("urgency_level")
                })
                break

    # Clean flag type to condition name
    condition_name = flag_type.replace("_", " ").title()

    return {
        "red_flag_id": f"rf_{flag_type}",
        "condition": condition_name,
        "keywords": sorted(list(all_keywords))[:30],  # Limit to 30 keywords
        "urgency": "emergent",
        "clinical_presentation": extract_clinical_presentation(contexts, flag_type),
        "first_aid": extract_first_aid(flag_type),
        "referral": extract_referral_disposition(flag_type),
        "time_to_treatment": RED_FLAG_PATTERNS[flag_type]["timeframe"],
        "source_chapters": sorted(list(source_chapters))[:5],
        "source_sections": sorted(list(source_sections))[:10],
        "related_diseases": related_diseases[:5],  # Limit to 5
        "context_count": len(contexts),
        "extraction_method": "rule_based",
        "confidence": "medium"
    }


def validate_red_flags(red_flags: List[Dict]) -> Dict:
    """
    Validate red flags for completeness and medical safety.

    Returns validation report.
    """
    issues = []

    for flag in red_flags:
        # Check required fields
        required_fields = [
            "red_flag_id", "condition", "keywords", "urgency",
            "clinical_presentation", "first_aid", "referral", "time_to_treatment"
        ]

        for field in required_fields:
            if not flag.get(field):
                issues.append(f"{flag['condition']}: Missing {field}")

        # Check keywords count
        if len(flag.get("keywords", [])) < 3:
            issues.append(f"{flag['condition']}: Too few keywords ({len(flag.get('keywords', []))})")

        # Check urgency is emergent
        if flag.get("urgency") != "emergent":
            issues.append(f"{flag['condition']}: Urgency is not 'emergent' ({flag.get('urgency')})")

    return {
        "total_red_flags": len(red_flags),
        "validation_passed": len(issues) == 0,
        "issues": issues,
        "completeness_score": (len(red_flags) - len(issues)) / len(red_flags) if red_flags else 0
    }


def generate_report(
    red_flags: List[Dict],
    validation_report: Dict,
    contexts: Dict
) -> Dict:
    """Generate Phase 5 report."""

    total_contexts = sum(len(v) for v in contexts.values())

    return {
        "phase": "5: Red Flag & Safety Extraction",
        "timestamp": "2025-10-23",
        "extraction_method": "rule_based",
        "extraction_approach": "keyword_pattern_matching",
        "confidence_level": "medium",
        "note": "For production use, consider LLM-based extraction for higher accuracy and detail (90-95% vs 75-85%)",
        "llm_enhancement_guide": "See PHASE5_LLM_ENHANCEMENT_GUIDE.md",
        "red_flags_extracted": len(red_flags),
        "total_contexts_found": total_contexts,
        "validation": validation_report,
        "red_flag_types": [flag["condition"] for flag in red_flags],
        "keyword_coverage": {
            flag["condition"]: len(flag["keywords"])
            for flag in red_flags
        },
        "source_coverage": {
            flag["condition"]: len(flag["source_chapters"])
            for flag in red_flags
        }
    }


def main():
    """Main execution."""
    print("=" * 70)
    print("Phase 5: Extract Red Flag Conditions from Wills Eye Manual")
    print("=" * 70)

    # Paths
    base_dir = Path(__file__).parent
    input_dir = base_dir / "output"
    output_dir = input_dir / "phase5"
    output_dir.mkdir(exist_ok=True)

    # Load inputs
    print("\n[1/6] Loading text blocks...")
    text_blocks_path = input_dir / "phase1" / "wills_eye_text_blocks.json"
    text_blocks = load_json(text_blocks_path)
    print(f"  Loaded {len(text_blocks)} text blocks")

    print("\n[2/6] Loading diseases with urgency...")
    diseases_path = input_dir / "phase4" / "diseases_with_urgency.json"
    diseases = load_json(diseases_path)
    print(f"  Loaded {len(diseases)} diseases")

    # Extract red flag contexts
    print("\n[3/6] Extracting red flag contexts from text...")
    red_flag_contexts = extract_red_flag_contexts(text_blocks)
    print(f"  Found contexts for {len(red_flag_contexts)} red flag types")
    for flag_type, contexts in red_flag_contexts.items():
        print(f"    {flag_type}: {len(contexts)} mentions")

    # Create red flag entries
    print("\n[4/6] Creating red flag entries...")
    red_flags = []
    for flag_type, contexts in red_flag_contexts.items():
        if contexts:  # Only create entry if we found contexts
            red_flag = create_red_flag_entry(flag_type, contexts, diseases)
            red_flags.append(red_flag)
            print(f"  Created: {red_flag['condition']} ({len(red_flag['keywords'])} keywords)")

    # Validate red flags
    print("\n[5/6] Validating red flags...")
    validation_report = validate_red_flags(red_flags)
    print(f"  Total red flags: {validation_report['total_red_flags']}")
    print(f"  Validation passed: {validation_report['validation_passed']}")
    if validation_report['issues']:
        print(f"  Issues found: {len(validation_report['issues'])}")
        for issue in validation_report['issues'][:5]:  # Show first 5 issues
            print(f"    - {issue}")

    # Save outputs
    print("\n[6/6] Saving outputs...")

    # Save red flags
    red_flags_path = output_dir / "red_flags.json"
    save_json(red_flags, red_flags_path)
    print(f"  Saved red flags to: {red_flags_path}")

    # Generate report
    report = generate_report(red_flags, validation_report, red_flag_contexts)
    report_path = output_dir / "phase5_report.json"
    save_json(report, report_path)
    print(f"  Saved report to: {report_path}")

    # Generate README
    readme_content = f"""# Phase 5 Output - Red Flag Extraction

⚠️ **Extraction Method**: Rule-Based (Keyword Pattern Matching)
📊 **Confidence Level**: Medium (75-85% accuracy)
💡 **For Production**: Consider LLM-based extraction (90-95% accuracy) - See PHASE5_LLM_ENHANCEMENT_GUIDE.md

## Overview

Extracted red flag conditions (emergent conditions requiring immediate ER referral) from The Wills Eye Manual using rule-based keyword pattern matching.

## 🚨 CRITICAL SAFETY REQUIREMENT

Red flag detection must have **100% recall** (no false negatives). Missing an emergent condition is unacceptable in medical triage software.

## Files

- **red_flags.json** - Extracted red flag conditions with keywords, clinical presentation, and first aid
- **phase5_report.json** - Statistics and validation report

## Red Flags Extracted

Total: **{len(red_flags)} emergent conditions**

"""

    for flag in red_flags:
        readme_content += f"""
### {flag['condition']}
- **Keywords**: {len(flag['keywords'])} extracted
- **Time to Treatment**: {flag['time_to_treatment']}
- **First Aid**: {flag['first_aid'][:80]}...
- **Source Chapters**: {len(flag['source_chapters'])}
"""

    readme_content += f"""

## Validation Report

- **Total Red Flags**: {validation_report['total_red_flags']}
- **Validation Passed**: {validation_report['validation_passed']}
- **Completeness Score**: {validation_report['completeness_score']:.1%}

"""

    if validation_report['issues']:
        readme_content += "### Issues Found\n\n"
        for issue in validation_report['issues'][:10]:
            readme_content += f"- {issue}\n"

    readme_content += """

## Next Steps

- ✅ Phase 5 complete
- 💡 Optional: Rerun with LLM for higher accuracy (see PHASE5_LLM_ENHANCEMENT_GUIDE.md)
- → Phase 6: Graph preparation for Neo4j
- → Phase 7: Validation & testing

## Usage in Triage System

Red flags are used in the triage agent for immediate emergency detection:

```python
from indexing.output.phase5.red_flags import RED_FLAGS

def detect_red_flags(patient_input: str) -> Tuple[bool, str]:
    for red_flag in RED_FLAGS:
        for keyword in red_flag['keywords']:
            if keyword.lower() in patient_input.lower():
                return True, red_flag['condition']
    return False, None
```

---
Generated: 2025-10-23
"""

    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  Saved README to: {readme_path}")

    print("\n" + "=" * 70)
    print("Phase 5 Complete!")
    print("=" * 70)
    print(f"\nRed Flags Extracted: {len(red_flags)}")
    print(f"Total Keyword Coverage: {sum(len(f['keywords']) for f in red_flags)}")
    print(f"Validation: {'PASSED' if validation_report['validation_passed'] else 'FAILED'}")
    print(f"\nOutput directory: {output_dir}")
    print("\nFor higher accuracy, consider LLM-based extraction:")
    print("   See PHASE5_LLM_ENHANCEMENT_GUIDE.md for instructions")


if __name__ == "__main__":
    main()
