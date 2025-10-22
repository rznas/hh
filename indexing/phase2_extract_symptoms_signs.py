#!/usr/bin/env python3
"""
Phase 2.2: Extract Symptom and Sign Entities from Wills Eye Manual

Extracts symptoms (Chapter 1) and signs (Chapter 2) as separate entity types.
These are critical for differential diagnosis in the triage system.

Outputs: symptoms.json, signs.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Common symptom keywords (patient-reported)
SYMPTOM_KEYWORDS = {
    'pain', 'ache', 'burning', 'itching', 'discharge', 'tearing',
    'dryness', 'blurred vision', 'decreased vision', 'vision loss',
    'double vision', 'diplopia', 'floaters', 'flashes', 'spots',
    'halos', 'glare', 'photophobia', 'light sensitivity',
    'redness', 'swelling', 'crusting', 'foreign body sensation',
    'headache', 'nausea', 'vomiting'
}

# Common sign keywords (clinician-observed)
SIGN_KEYWORDS = {
    'edema', 'hemorrhage', 'injection', 'chemosis', 'proptosis',
    'ptosis', 'exotropia', 'esotropia', 'nystagmus', 'anisocoria',
    'mydriasis', 'miosis', 'opacity', 'infiltrate', 'ulcer',
    'neovascularization', 'vascularization', 'scarring', 'atrophy',
    'hypertrophy', 'membrane', 'deposit', 'precipitate'
}

def extract_symptom_sign_from_heading(heading: str, chapter: int) -> Dict:
    """Extract symptom/sign entity from section heading."""
    # Chapter 1 headings are symptoms, Chapter 2 headings are signs
    entity_type = 'symptom' if chapter == 1 else 'sign'

    # Clean heading
    heading_clean = heading.strip()

    # Skip generic headings
    if heading_clean.lower() in ['differential diagnosis of ocular symptoms',
                                   'differential diagnosis of ocular signs']:
        return None

    # Determine if red flag based on keywords
    red_flag_keywords = [
        'sudden', 'loss', 'chemical', 'trauma', 'penetrating',
        'severe pain', 'vision loss', 'decreased vision',
        'flashes', 'floaters', 'curtain', 'shadow'
    ]

    is_red_flag = any(kw in heading_clean.lower() for kw in red_flag_keywords)

    return {
        'name': heading_clean,
        'name_normalized': heading_clean.lower(),
        'type': entity_type,
        'red_flag': is_red_flag
    }

def extract_symptoms_signs_from_lists(lists: List[Dict]) -> Dict[str, List[str]]:
    """Extract symptom/sign variations from list items."""
    symptom_variations = defaultdict(list)

    for lst in lists:
        if lst['chapter_number'] not in [1, 2]:
            continue

        entity_type = 'symptom' if lst['chapter_number'] == 1 else 'sign'

        for item in lst['items']:
            # List items often describe variations or related conditions
            item_clean = item.strip()
            if len(item_clean) > 5:
                # Try to extract the core symptom/sign
                symptom_variations[entity_type].append(item_clean)

    return dict(symptom_variations)

def build_symptom_sign_entities(text_blocks: List[Dict], lists: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Build symptom and sign entity objects."""

    symptoms = []
    signs = []

    # Track entities by chapter
    entities_by_chapter = defaultdict(list)

    # Extract from list section headings in Chapters 1 and 2
    print("\nExtracting from Chapter 1 & 2 list sections...")
    seen_headings = set()

    for lst in lists:
        if lst['chapter_number'] not in [1, 2]:
            continue

        # Each unique section heading is likely a symptom/sign
        section = lst['section']

        if section not in seen_headings:
            seen_headings.add(section)
            entity = extract_symptom_sign_from_heading(section, lst['chapter_number'])

            if entity:
                entities_by_chapter[lst['chapter_number']].append({
                    **entity,
                    'section': section,
                    'chapter': lst['chapter_number']
                })

    # Build symptom entities (Chapter 1)
    print(f"Building symptom entities from Chapter 1...")
    symptom_id = 1
    for entity_data in entities_by_chapter[1]:
        # Collect related lists for this symptom
        related_lists = [
            lst for lst in lists
            if lst['chapter_number'] == 1 and
            entity_data['name_normalized'] in lst['section'].lower()
        ]

        # Extract differential diagnoses associated with this symptom
        associated_conditions = []
        for lst in related_lists:
            if lst['list_type'] == 'differential_diagnosis':
                associated_conditions.extend(lst['items'][:5])  # Top 5

        symptom = {
            'entity_id': f"symptom_{symptom_id:03d}",
            'name': entity_data['name'],
            'name_normalized': entity_data['name_normalized'],
            'type': 'symptom',
            'category': 'ocular',  # All from Wills Eye Manual
            'red_flag': entity_data['red_flag'],
            'chapter': 1,
            'section': entity_data['section'],
            'associated_conditions': associated_conditions[:5],
            'variations': []  # To be populated with synonyms later
        }

        symptoms.append(symptom)
        symptom_id += 1

    # Build sign entities (Chapter 2)
    print(f"Building sign entities from Chapter 2...")
    sign_id = 1
    for entity_data in entities_by_chapter[2]:
        # Collect related lists for this sign
        related_lists = [
            lst for lst in lists
            if lst['chapter_number'] == 2 and
            entity_data['name_normalized'] in lst['section'].lower()
        ]

        # Extract differential diagnoses associated with this sign
        associated_conditions = []
        for lst in related_lists:
            if lst['list_type'] == 'differential_diagnosis':
                associated_conditions.extend(lst['items'][:5])

        sign = {
            'entity_id': f"sign_{sign_id:03d}",
            'name': entity_data['name'],
            'name_normalized': entity_data['name_normalized'],
            'type': 'sign',
            'category': 'ocular',
            'red_flag': entity_data['red_flag'],
            'chapter': 2,
            'section': entity_data['section'],
            'associated_conditions': associated_conditions[:5],
            'variations': []
        }

        signs.append(sign)
        sign_id += 1

    return symptoms, signs

def main():
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "indexing" / "output" / "phase1"
    output_dir = base_dir / "indexing" / "output" / "phase2"

    print("=" * 60)
    print("Phase 2.2: Symptom & Sign Entity Extraction")
    print("=" * 60)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(input_dir / "wills_eye_text_blocks.json") as f:
        text_blocks = json.load(f)

    with open(input_dir / "wills_eye_lists.json") as f:
        lists = json.load(f)

    # Filter for Chapters 1 and 2
    ch1_blocks = [b for b in text_blocks if b['chapter_number'] == 1]
    ch2_blocks = [b for b in text_blocks if b['chapter_number'] == 2]

    print(f"  Chapter 1 (Symptoms): {len(ch1_blocks)} blocks")
    print(f"  Chapter 2 (Signs): {len(ch2_blocks)} blocks")

    # Extract entities
    print("\n" + "=" * 60)
    symptoms, signs = build_symptom_sign_entities(text_blocks, lists)

    print(f"\n✓ Extracted {len(symptoms)} symptom entities")
    print(f"✓ Extracted {len(signs)} sign entities")

    # Count red flags
    symptom_red_flags = sum(1 for s in symptoms if s['red_flag'])
    sign_red_flags = sum(1 for s in signs if s['red_flag'])

    print(f"\nRed flag symptoms: {symptom_red_flags}")
    print(f"Red flag signs: {sign_red_flags}")

    # Save symptoms
    output_file = output_dir / "symptoms.json"
    with open(output_file, 'w') as f:
        json.dump(symptoms, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved: {output_file.name}")

    # Save signs
    output_file = output_dir / "signs.json"
    with open(output_file, 'w') as f:
        json.dump(signs, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {output_file.name}")

    # Generate report
    report = {
        'phase': '2.2 - Symptom & Sign Entity Extraction',
        'total_symptoms': len(symptoms),
        'total_signs': len(signs),
        'red_flag_symptoms': symptom_red_flags,
        'red_flag_signs': sign_red_flags,
        'sample_symptoms': [s['name'] for s in symptoms[:5]],
        'sample_signs': [s['name'] for s in signs[:5]]
    }

    report_file = output_dir / "phase2_2_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✓ Report: {report_file.name}")

    print("\n" + "=" * 60)
    print("Phase 2.2 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
