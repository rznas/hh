#!/usr/bin/env python3
"""
Phase 2.3: Extract Treatment/Procedure Entities from Wills Eye Manual (v2)

Enhanced version that extracts:
- Medications (topical, oral, systemic)
- Surgical procedures
- Laser procedures
- Diagnostic procedures

Input: Phase 1 outputs (lists, text blocks)
Output: treatments.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent
PHASE1_DIR = BASE_DIR / "output" / "phase1"
PHASE2_DIR = BASE_DIR / "output" / "phase2"

# Known medications (ophthalmic drugs)
KNOWN_MEDICATIONS = {
    # Antibiotics
    'ciprofloxacin', 'moxifloxacin', 'gatifloxacin', 'ofloxacin', 'levofloxacin',
    'tobramycin', 'gentamicin', 'erythromycin', 'azithromycin', 'vancomycin',
    'cefazolin', 'ceftazidime', 'fortified tobramycin', 'fortified vancomycin',
    'polymyxin', 'bacitracin', 'neomycin', 'trimethoprim',

    # Corticosteroids
    'prednisolone', 'dexamethasone', 'fluorometholone', 'loteprednol',
    'difluprednate', 'prednisone', 'methylprednisolone', 'triamcinolone',

    # Antiglaucoma
    'timolol', 'betaxolol', 'levobunolol', 'carteolol',
    'latanoprost', 'bimatoprost', 'travoprost', 'tafluprost',
    'brimonidine', 'apraclonidine',
    'dorzolamide', 'brinzolamide', 'acetazolamide', 'methazolamide',
    'pilocarpine', 'carbachol',

    # Cycloplegics/Mydriatics
    'atropine', 'homatropine', 'scopolamine', 'cyclopentolate', 'tropicamide',
    'phenylephrine',

    # Antivirals
    'acyclovir', 'valacyclovir', 'famciclovir', 'ganciclovir', 'valganciclovir',
    'foscarnet', 'cidofovir', 'trifluridine',

    # Antifungals
    'natamycin', 'amphotericin', 'fluconazole', 'voriconazole', 'itraconazole',

    # NSAIDs
    'ketorolac', 'bromfenac', 'nepafenac', 'diclofenac', 'flurbiprofen',
    'ibuprofen', 'indomethacin',

    # Lubricants
    'artificial tears', 'carboxymethylcellulose', 'hydroxypropyl methylcellulose',
    'hyaluronic acid', 'polyethylene glycol', 'propylene glycol',
    'cyclosporine', 'lifitegrast',

    # Antihistamines/Mast cell stabilizers
    'olopatadine', 'ketotifen', 'azelastine', 'epinastine', 'alcaftadine',
    'cromolyn', 'nedocromil', 'lodoxamide',

    # Other
    'bevacizumab', 'ranibizumab', 'aflibercept', 'pegaptanib',
    'verteporfin', 'fluorescein', 'indocyanine green',
    'proparacaine', 'tetracaine', 'lidocaine',
}

# Known procedures
KNOWN_PROCEDURES = {
    # Surgical
    'vitrectomy', 'pars plana vitrectomy', 'ppv',
    'keratoplasty', 'penetrating keratoplasty', 'corneal transplant',
    'trabeculectomy', 'tube shunt', 'ahmed valve', 'baerveldt implant',
    'cataract extraction', 'phacoemulsification', 'iol implantation',
    'scleral buckle', 'pneumatic retinopexy',
    'evisceration', 'enucleation',
    'repair', 'primary repair', 'corneal repair', 'scleral repair',
    'laceration repair', 'globe repair',
    'drainage', 'abscess drainage', 'hyphema evacuation',
    'foreign body removal', 'intraocular foreign body removal',
    'debridement', 'epithelial debridement',
    'tarsorrhaphy',

    # Laser procedures
    'photocoagulation', 'panretinal photocoagulation', 'prp',
    'focal laser', 'laser trabeculoplasty', 'selective laser trabeculoplasty', 'slt',
    'argon laser trabeculoplasty', 'alt',
    'laser iridotomy', 'peripheral iridotomy', 'yag iridotomy',
    'yag capsulotomy', 'laser capsulotomy',
    'cyclophotoco agulation', 'cyclophotocoagulation',
    'photodynamic therapy', 'pdt',

    # Diagnostic
    'culture', 'corneal culture', 'vitreous culture',
    'scraping', 'corneal scraping',
    'biopsy', 'conjunctival biopsy', 'corneal biopsy',
    'paracentesis', 'anterior chamber tap',
    'vitreous tap',
    'fluorescein angiography', 'fa',
    'indocyanine green angiography', 'icg',
    'oct', 'optical coherence tomography',
    'ultrasound', 'b-scan', 'a-scan',
    'imaging', 'fundus photography',
}


def normalize_name(name: str) -> str:
    """Normalize entity name."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    # Remove dosage information
    name = re.sub(r'\d+%|\d+mg|\d+ml', '', name)
    name = name.strip()
    return name


def extract_from_medication_lists(lists_data: List[Dict]) -> Dict[str, Dict]:
    """Extract medication entities from medication lists."""
    medications = {}
    med_mentions = defaultdict(int)
    med_chapters = defaultdict(set)
    med_sections = defaultdict(set)

    med_lists = [lst for lst in lists_data if lst['list_type'] == 'medication']

    print(f"Processing {len(med_lists)} medication lists...")

    for lst in med_lists:
        chapter = lst['chapter_number']
        section = lst['section']

        for item in lst['items']:
            # Extract medication name (before dosage or parentheses)
            med_name = item.strip()

            # Remove dosage information
            med_name = re.split(r'[\(\d]', med_name)[0].strip()
            med_name = re.sub(r'\s+q\.?\s*\d+', '', med_name, flags=re.IGNORECASE)

            normalized = normalize_name(med_name)

            if len(normalized) < 3:
                continue

            # Skip generic terms
            if normalized in ['and', 'or', 'with', 'without']:
                continue

            med_mentions[normalized] += 1
            med_chapters[normalized].add(chapter)
            med_sections[normalized].add(section)

    # Create entities
    entity_id = 1
    for med_name, mention_count in med_mentions.items():
        if mention_count >= 1:  # Include all medications found in lists
            medications[med_name] = {
                'entity_id': f'treatment_{entity_id:03d}',
                'name': med_name.title(),
                'name_normalized': med_name,
                'type': 'medication',
                'category': 'pharmacological',
                'chapters': sorted(med_chapters[med_name]),
                'sections': sorted(med_sections[med_name]),
                'description': f'Medication extracted from treatment lists',
                'mention_count': mention_count,
            }
            entity_id += 1

    return medications


def extract_from_treatment_lists(lists_data: List[Dict]) -> Dict[str, Dict]:
    """Extract both medications and procedures from treatment lists."""
    treatments = {}
    treatment_mentions = defaultdict(int)
    treatment_chapters = defaultdict(set)
    treatment_sections = defaultdict(set)
    treatment_types = defaultdict(str)

    treatment_lists = [lst for lst in lists_data if lst['list_type'] == 'treatment']

    print(f"Processing {len(treatment_lists)} treatment lists...")

    for lst in treatment_lists:
        chapter = lst['chapter_number']
        section = lst['section']

        for item in lst['items']:
            item_lower = item.lower()

            # Check if it's a known medication
            for known_med in KNOWN_MEDICATIONS:
                if known_med in item_lower:
                    normalized = normalize_name(known_med)
                    treatment_mentions[normalized] += 1
                    treatment_chapters[normalized].add(chapter)
                    treatment_sections[normalized].add(section)
                    treatment_types[normalized] = 'medication'

            # Check if it's a known procedure
            for known_proc in KNOWN_PROCEDURES:
                if known_proc in item_lower:
                    normalized = normalize_name(known_proc)
                    treatment_mentions[normalized] += 1
                    treatment_chapters[normalized].add(chapter)
                    treatment_sections[normalized].add(section)
                    treatment_types[normalized] = 'procedure'

    # Create entities
    entity_id = 1000  # Start at 1000 to avoid conflicts with medication lists
    for treatment_name, mention_count in treatment_mentions.items():
        if mention_count >= 2:
            treatment_type = treatment_types[treatment_name]
            category = 'pharmacological' if treatment_type == 'medication' else 'procedural'

            treatments[treatment_name] = {
                'entity_id': f'treatment_{entity_id:03d}',
                'name': treatment_name.title(),
                'name_normalized': treatment_name,
                'type': treatment_type,
                'category': category,
                'chapters': sorted(treatment_chapters[treatment_name]),
                'sections': sorted(treatment_sections[treatment_name]),
                'description': f'{treatment_type.title()} extracted from treatment lists',
                'mention_count': mention_count,
            }
            entity_id += 1

    return treatments


def extract_from_procedure_lists(lists_data: List[Dict]) -> Dict[str, Dict]:
    """Extract procedures from procedure lists."""
    procedures = {}
    proc_mentions = defaultdict(int)
    proc_chapters = defaultdict(set)
    proc_sections = defaultdict(set)

    proc_lists = [lst for lst in lists_data if lst['list_type'] == 'procedure']

    print(f"Processing {len(proc_lists)} procedure lists...")

    for lst in proc_lists:
        chapter = lst['chapter_number']
        section = lst['section']

        for item in lst['items']:
            # Clean procedure name
            proc_name = item.strip()

            # Remove descriptive text after colon or parentheses
            if ':' in proc_name:
                proc_name = proc_name.split(':')[0]
            proc_name = re.split(r'[\(\[]', proc_name)[0]

            normalized = normalize_name(proc_name)

            if len(normalized) < 3:
                continue

            proc_mentions[normalized] += 1
            proc_chapters[normalized].add(chapter)
            proc_sections[normalized].add(section)

    # Create entities
    entity_id = 2000  # Start at 2000
    for proc_name, mention_count in proc_mentions.items():
        if mention_count >= 1:
            procedures[proc_name] = {
                'entity_id': f'treatment_{entity_id:03d}',
                'name': proc_name.title(),
                'name_normalized': proc_name,
                'type': 'procedure',
                'category': 'procedural',
                'chapters': sorted(proc_chapters[proc_name]),
                'sections': sorted(proc_sections[proc_name]),
                'description': f'Procedure extracted from procedure lists',
                'mention_count': mention_count,
            }
            entity_id += 1

    return procedures


def merge_treatments(treatment_dicts: List[Dict[str, Dict]]) -> List[Dict]:
    """Merge treatments from multiple sources, avoiding duplicates."""
    merged = {}

    for treatment_dict in treatment_dicts:
        for key, treatment in treatment_dict.items():
            if key not in merged:
                merged[key] = treatment
            else:
                # Merge information
                existing = merged[key]
                existing['mention_count'] += treatment.get('mention_count', 1)

                # Merge chapters
                existing_chapters = set(existing.get('chapters', []))
                new_chapters = set(treatment.get('chapters', []))
                existing['chapters'] = sorted(existing_chapters | new_chapters)

                # Merge sections
                existing_sections = set(existing.get('sections', []))
                new_sections = set(treatment.get('sections', []))
                existing['sections'] = sorted(existing_sections | new_sections)

    # Convert to list and renumber entity IDs
    treatments_list = sorted(merged.values(), key=lambda x: (x['type'], x['name_normalized']))

    # Renumber entity IDs sequentially
    for idx, treatment in enumerate(treatments_list, start=1):
        treatment['entity_id'] = f'treatment_{idx:03d}'

    return treatments_list


def main():
    """Main extraction pipeline."""
    print("=" * 60)
    print("Phase 2.3: Treatment/Procedure Entity Extraction (v2)")
    print("=" * 60)

    # Create output directory
    PHASE2_DIR.mkdir(parents=True, exist_ok=True)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(PHASE1_DIR / "wills_eye_lists.json", 'r', encoding='utf-8') as f:
        lists_data = json.load(f)

    print(f"Loaded {len(lists_data)} lists")

    # Step 1: Extract from medication lists
    print("\n" + "="*60)
    print("Step 1: Extracting from medication lists...")
    print("="*60)
    medications = extract_from_medication_lists(lists_data)
    print(f"Extracted {len(medications)} medications")

    # Step 2: Extract from treatment lists
    print("\n" + "="*60)
    print("Step 2: Extracting from treatment lists...")
    print("="*60)
    treatments = extract_from_treatment_lists(lists_data)
    print(f"Extracted {len(treatments)} treatments")

    # Step 3: Extract from procedure lists
    print("\n" + "="*60)
    print("Step 3: Extracting from procedure lists...")
    print("="*60)
    procedures = extract_from_procedure_lists(lists_data)
    print(f"Extracted {len(procedures)} procedures")

    # Merge all
    print("\n" + "="*60)
    print("Merging treatments...")
    print("="*60)
    treatments_list = merge_treatments([medications, treatments, procedures])
    print(f"Total unique treatments: {len(treatments_list)}")

    # Generate statistics
    print("\n" + "="*60)
    print("Statistics:")
    print("="*60)

    type_counts = defaultdict(int)
    for treatment in treatments_list:
        type_counts[treatment['type']] += 1

    print(f"Total treatment entities: {len(treatments_list)}")
    print(f"\nType distribution:")
    for treat_type, count in sorted(type_counts.items()):
        print(f"  {treat_type}: {count}")

    # Save treatments.json
    output_file = PHASE2_DIR / "treatments.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(treatments_list, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(treatments_list)} treatments to {output_file}")

    # Save report
    report = {
        'phase': '2.3 - Treatment/Procedure Entity Extraction (v2)',
        'total_entities': len(treatments_list),
        'type_distribution': dict(type_counts),
        'top_by_mentions': [
            {'name': t['name'], 'type': t['type'], 'mentions': t['mention_count']}
            for t in sorted(treatments_list, key=lambda x: x['mention_count'], reverse=True)[:20]
        ]
    }

    report_file = PHASE2_DIR / "phase2_3_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Saved report to {report_file}")

    print("\n" + "="*60)
    print("Phase 2.3 Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
