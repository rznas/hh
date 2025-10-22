#!/usr/bin/env python3
"""
Phase 2.1: Extract Disease/Condition Entities from Wills Eye Manual

Uses rule-based pattern matching to extract disease entities from:
- Text blocks (609 blocks from Phase 1)
- Differential diagnosis lists (48 lists)
- Section headings

Outputs: diseases.json with entity schema
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Common disease/condition suffixes and patterns
DISEASE_PATTERNS = [
    r'\b(\w+itis)\b',  # -itis (inflammation): keratitis, uveitis, conjunctivitis
    r'\b(\w+oma)\b',   # -oma (tumor): melanoma, glaucoma, retinoblastoma
    r'\b(\w+opathy)\b', # -opathy: retinopathy, neuropathy
    r'\b(\w+trophy)\b', # -trophy: dystrophy
    r'\b(\w+osis)\b',  # -osis: keratosis, necrosis
    r'\b(\w+edema)\b', # edema
    r'\b(\w+oedema)\b', # British spelling
    r'\b(\w+ syndrome)\b', # Named syndromes
    r'\b(\w+ disease)\b',  # Named diseases
]

# Known disease terms (seed list for validation)
KNOWN_DISEASES = {
    'keratitis', 'conjunctivitis', 'uveitis', 'glaucoma', 'cataract',
    'retinopathy', 'neuropathy', 'blepharitis', 'scleritis', 'episcleritis',
    'iritis', 'endophthalmitis', 'cellulitis', 'chalazion', 'hordeolum',
    'pterygium', 'pinguecula', 'melanoma', 'nevus', 'papilledema',
    'hyphema', 'hypopyon', 'vitreous hemorrhage', 'retinal detachment',
    'macular degeneration', 'diabetic retinopathy', 'hypertensive retinopathy',
    'corneal ulcer', 'corneal abrasion', 'chemical burn', 'thermal burn',
    'orbital cellulitis', 'preseptal cellulitis', 'optic neuritis',
    'papillitis', 'neovascularization', 'hemorrhage', 'infarction'
}

# Chapter-based severity mapping (simplified)
CHAPTER_SEVERITY = {
    1: 'varies',  # Symptoms - varies
    2: 'varies',  # Signs - varies
    3: 'emergent',  # Trauma - typically urgent/emergent
    4: 'urgent',    # Cornea - often urgent
    5: 'urgent',    # Conjunctiva/Sclera/Iris - often urgent
}

def normalize_disease_name(name: str) -> str:
    """Normalize disease name."""
    # Convert to lowercase
    name = name.lower().strip()
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    return name

def extract_diseases_from_text(text: str) -> Set[str]:
    """Extract disease names from text using patterns."""
    diseases = set()

    for pattern in DISEASE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            normalized = normalize_disease_name(match)
            # Filter out very short or generic terms
            if len(normalized) > 3 and not normalized.startswith('the '):
                diseases.add(normalized)

    # Also check for known diseases
    text_lower = text.lower()
    for known in KNOWN_DISEASES:
        if known in text_lower:
            diseases.add(known)

    return diseases

def extract_from_section_heading(heading: str) -> List[str]:
    """Extract disease from section heading (often the disease name itself)."""
    # Section headings are often the disease name
    heading_lower = normalize_disease_name(heading)

    # Skip generic headings
    generic_terms = ['unknown', 'differential', 'diagnosis', 'treatment',
                     'management', 'workup', 'etiology', 'general', 'overview']

    if any(term in heading_lower for term in generic_terms):
        return []

    # Check if it matches disease patterns or known diseases
    diseases = extract_diseases_from_text(heading)
    if diseases:
        return list(diseases)

    # If heading is relatively short and specific, it might be a disease name
    if len(heading.split()) <= 4 and len(heading) > 5:
        # Check if it's not a symptom description
        symptom_words = ['burning', 'pain', 'redness', 'discharge', 'swelling',
                         'vision', 'double', 'decreased', 'loss']
        if not any(word in heading_lower for word in symptom_words):
            return [heading_lower]

    return []

def build_disease_entities(text_blocks: List[Dict], lists: List[Dict]) -> List[Dict]:
    """Build disease entity objects from extracted data."""

    # Collect all disease mentions with context
    disease_mentions = defaultdict(lambda: {
        'chapters': set(),
        'sections': set(),
        'from_ddx': False,
        'from_heading': False,
        'contexts': []
    })

    # Extract from text blocks
    print("\nExtracting from text blocks...")
    for block in text_blocks:
        diseases = extract_diseases_from_text(block['text'])
        for disease in diseases:
            disease_mentions[disease]['chapters'].add(block['chapter_number'])
            disease_mentions[disease]['sections'].add(block['section_path'])
            disease_mentions[disease]['contexts'].append(block['text'][:200])

    # Extract from differential diagnosis lists (high confidence)
    print("Extracting from differential diagnosis lists...")
    ddx_lists = [lst for lst in lists if lst['list_type'] == 'differential_diagnosis']
    for lst in ddx_lists:
        for item in lst['items']:
            # List items in DDx are often disease names
            diseases = extract_diseases_from_text(item)
            # Also add the item itself if it looks like a disease
            item_normalized = normalize_disease_name(item)
            if len(item_normalized) > 3:
                diseases.add(item_normalized)

            for disease in diseases:
                disease_mentions[disease]['chapters'].add(lst['chapter_number'])
                disease_mentions[disease]['sections'].add(lst['section'])
                disease_mentions[disease]['from_ddx'] = True
                disease_mentions[disease]['contexts'].append(f"DDx: {item[:200]}")

    # Extract from section headings
    print("Extracting from section headings...")
    for block in text_blocks:
        section_diseases = extract_from_section_heading(block['section_path'])
        for disease in section_diseases:
            disease_mentions[disease]['chapters'].add(block['chapter_number'])
            disease_mentions[disease]['sections'].add(block['section_path'])
            disease_mentions[disease]['from_heading'] = True

    # Build entity objects
    entities = []
    entity_id = 1

    for disease_name, data in sorted(disease_mentions.items()):
        # Filter out likely false positives (mentioned only once in non-DDx context)
        if len(data['chapters']) == 1 and not data['from_ddx'] and not data['from_heading']:
            continue

        # Determine severity based on chapters
        chapters = sorted(data['chapters'])
        if 3 in chapters:  # Trauma chapter
            severity = 'emergent'
        elif any(ch in [4, 5] for ch in chapters):  # Cornea, Conjunctiva
            severity = 'urgent'
        else:
            severity = 'non-urgent'

        # Check if likely a red flag (appears in trauma or multiple urgent chapters)
        red_flag = (3 in chapters) or (len([ch for ch in chapters if ch in [3, 4]]) >= 2)

        entity = {
            'entity_id': f"disease_{entity_id:03d}",
            'name': disease_name.title(),  # Proper case
            'name_normalized': disease_name,
            'synonyms': [],  # To be populated later
            'icd_10': None,  # To be mapped in Phase 4
            'snomed_ct': None,
            'description': data['contexts'][0][:150] if data['contexts'] else '',
            'chapters': chapters,
            'sections': sorted(data['sections'])[:3],  # Top 3 sections
            'severity': severity,
            'red_flag': red_flag,
            'from_differential_diagnosis': data['from_ddx'],
            'from_section_heading': data['from_heading'],
            'mention_count': len(data['contexts'])
        }

        entities.append(entity)
        entity_id += 1

    return entities

def main():
    base_dir = Path(__file__).parent.parent
    input_dir = base_dir / "indexing" / "output" / "phase1"
    output_dir = base_dir / "indexing" / "output" / "phase2"

    print("=" * 60)
    print("Phase 2.1: Disease Entity Extraction")
    print("=" * 60)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(input_dir / "wills_eye_text_blocks.json") as f:
        text_blocks = json.load(f)
    print(f"  Loaded {len(text_blocks)} text blocks")

    with open(input_dir / "wills_eye_lists.json") as f:
        lists = json.load(f)
    print(f"  Loaded {len(lists)} lists")

    ddx_count = len([l for l in lists if l['list_type'] == 'differential_diagnosis'])
    print(f"    - {ddx_count} differential diagnosis lists")

    # Extract disease entities
    print("\n" + "=" * 60)
    entities = build_disease_entities(text_blocks, lists)

    print(f"\n✓ Extracted {len(entities)} disease entities")

    # Statistics
    severity_counts = defaultdict(int)
    red_flag_count = 0
    from_ddx_count = 0

    for entity in entities:
        severity_counts[entity['severity']] += 1
        if entity['red_flag']:
            red_flag_count += 1
        if entity['from_differential_diagnosis']:
            from_ddx_count += 1

    print(f"\nSeverity distribution:")
    for severity, count in sorted(severity_counts.items()):
        print(f"  {severity}: {count}")
    print(f"\nRed flag diseases: {red_flag_count}")
    print(f"From differential diagnosis: {from_ddx_count}")

    # Save entities
    output_file = output_dir / "diseases.json"
    with open(output_file, 'w') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved: {output_file.name}")

    # Generate report
    report = {
        'phase': '2.1 - Disease Entity Extraction',
        'total_entities': len(entities),
        'severity_distribution': dict(severity_counts),
        'red_flag_count': red_flag_count,
        'from_differential_diagnosis': from_ddx_count,
        'top_diseases_by_mentions': [
            {'name': e['name'], 'mentions': e['mention_count']}
            for e in sorted(entities, key=lambda x: x['mention_count'], reverse=True)[:10]
        ]
    }

    report_file = output_dir / "phase2_1_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✓ Report: {report_file.name}")

    print("\n" + "=" * 60)
    print("Phase 2.1 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
