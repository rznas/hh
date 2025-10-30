#!/usr/bin/env python3
"""
Phase 2.3: Extract Treatment and Procedure Entities from Wills Eye Manual

Extracts:
- Medications (from medication lists)
- Procedures (surgical and diagnostic)
- Non-pharmacological treatments

Output: treatments.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Medication indicators
MEDICATION_PATTERNS = [
    r'\b(\w+)\s+\d+%',  # e.g., "prednisolone 1%"
    r'\b(\w+)\s+\d+\s*mg',  # e.g., "500 mg"
    r'\b(\w+)\s+drops?\b',  # e.g., "antibiotic drops"
    r'\b(topical|oral|IV|intravitreal|subconjunctival)\s+(\w+)',
]

# Common medication classes/types
MEDICATION_KEYWORDS = {
    'antibiotic', 'steroid', 'corticosteroid', 'nsaid', 'cycloplegic',
    'mydriatic', 'antiviral', 'antifungal', 'antiglaucoma', 'lubricant',
    'artificial tears', 'ointment', 'gel', 'solution', 'suspension',
    'prednisolone', 'dexamethasone', 'fluorometholone', 'tobramycin',
    'ciprofloxacin', 'ofloxacin', 'moxifloxacin', 'gatifloxacin',
    'erythromycin', 'bacitracin', 'timolol', 'latanoprost', 'brimonidine',
    'dorzolamide', 'acetazolamide', 'mannitol', 'hypertonic saline'
}

# Procedure keywords
PROCEDURE_KEYWORDS = {
    'surgery', 'repair', 'removal', 'excision', 'biopsy', 'transplant',
    'laser', 'photocoagulation', 'cryotherapy', 'drainage', 'irrigation',
    'debridement', 'suture', 'graft', 'keratoplasty', 'vitrectomy',
    'cataract extraction', 'trabeculectomy', 'iridotomy', 'capsulotomy',
    'injection', 'aspiration', 'culture', 'scraping'
}

def extract_medications_from_lists(lists: List[Dict]) -> List[Dict]:
    """Extract medication entities from medication lists."""
    medications = defaultdict(lambda: {
        'chapters': set(),
        'sections': set(),
        'contexts': []
    })

    med_lists = [lst for lst in lists if lst['list_type'] == 'medication']

    for lst in med_lists:
        for item in lst['items']:
            # Try to extract medication name
            item_lower = item.lower()

            # Check for known medications
            for med_keyword in MEDICATION_KEYWORDS:
                if med_keyword in item_lower:
                    medications[med_keyword]['chapters'].add(lst['chapter_number'])
                    medications[med_keyword]['sections'].add(lst['section'])
                    medications[med_keyword]['contexts'].append(item[:150])

            # Extract using patterns
            for pattern in MEDICATION_PATTERNS:
                matches = re.findall(pattern, item_lower, re.IGNORECASE)
                for match in matches:
                    med_name = match if isinstance(match, str) else match[-1]
                    if len(med_name) > 3:
                        medications[med_name]['chapters'].add(lst['chapter_number'])
                        medications[med_name]['sections'].add(lst['section'])
                        medications[med_name]['contexts'].append(item[:150])

    return medications

def extract_procedures_from_lists(lists: List[Dict]) -> List[Dict]:
    """Extract procedure entities from procedure and treatment lists."""
    procedures = defaultdict(lambda: {
        'chapters': set(),
        'sections': set(),
        'contexts': []
    })

    proc_lists = [lst for lst in lists if lst['list_type'] in ['procedure', 'treatment']]

    for lst in proc_lists:
        for item in lst['items']:
            item_lower = item.lower()

            # Check for known procedures
            for proc_keyword in PROCEDURE_KEYWORDS:
                if proc_keyword in item_lower:
                    procedures[proc_keyword]['chapters'].add(lst['chapter_number'])
                    procedures[proc_keyword]['sections'].add(lst['section'])
                    procedures[proc_keyword]['contexts'].append(item[:150])

    return procedures

def build_treatment_entities(lists: List[Dict]) -> List[Dict]:
    """Build treatment entity objects (medications + procedures)."""

    print("\nExtracting medications from lists...")
    medications_data = extract_medications_from_lists(lists)
    print(f"  Found {len(medications_data)} medication entities")

    print("Extracting procedures from lists...")
    procedures_data = extract_procedures_from_lists(lists)
    print(f"  Found {len(procedures_data)} procedure entities")

    # Build entities
    entities = []
    entity_id = 1

    # Add medications
    for med_name, data in sorted(medications_data.items()):
        # Filter rare mentions
        if len(data['contexts']) < 2:
            continue

        entity = {
            'entity_id': f"treatment_{entity_id:03d}",
            'name': med_name.title(),
            'name_normalized': med_name,
            'type': 'medication',
            'category': 'pharmacological',
            'chapters': sorted(data['chapters']),
            'sections': sorted(data['sections'])[:3],
            'description': data['contexts'][0],
            'mention_count': len(data['contexts'])
        }

        entities.append(entity)
        entity_id += 1

    # Add procedures
    for proc_name, data in sorted(procedures_data.items()):
        # Filter rare mentions
        if len(data['contexts']) < 1:
            continue

        entity = {
            'entity_id': f"treatment_{entity_id:03d}",
            'name': proc_name.title(),
            'name_normalized': proc_name,
            'type': 'procedure',
            'category': 'surgical' if 'surgery' in proc_name or 'laser' in proc_name else 'diagnostic',
            'chapters': sorted(data['chapters']),
            'sections': sorted(data['sections'])[:3],
            'description': data['contexts'][0],
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
    print("Phase 2.3: Treatment & Procedure Entity Extraction")
    print("=" * 60)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(input_dir / "wills_eye_lists.json") as f:
        lists = json.load(f)

    med_lists = [l for l in lists if l['list_type'] == 'medication']
    treat_lists = [l for l in lists if l['list_type'] == 'treatment']
    proc_lists = [l for l in lists if l['list_type'] == 'procedure']

    print(f"  Medication lists: {len(med_lists)}")
    print(f"  Treatment lists: {len(treat_lists)}")
    print(f"  Procedure lists: {len(proc_lists)}")

    # Extract entities
    print("\n" + "=" * 60)
    entities = build_treatment_entities(lists)

    # Count by type
    med_count = sum(1 for e in entities if e['type'] == 'medication')
    proc_count = sum(1 for e in entities if e['type'] == 'procedure')

    print(f"\n✓ Extracted {len(entities)} treatment entities")
    print(f"  Medications: {med_count}")
    print(f"  Procedures: {proc_count}")

    # Save entities
    output_file = output_dir / "treatments.json"
    with open(output_file, 'w') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved: {output_file.name}")

    # Generate report
    report = {
        'phase': '2.3 - Treatment & Procedure Entity Extraction',
        'total_entities': len(entities),
        'medications': med_count,
        'procedures': proc_count,
        'sample_medications': [e['name'] for e in entities if e['type'] == 'medication'][:5],
        'sample_procedures': [e['name'] for e in entities if e['type'] == 'procedure'][:5]
    }

    report_file = output_dir / "phase2_3_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✓ Report: {report_file.name}")

    print("\n" + "=" * 60)
    print("Phase 2.3 Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
