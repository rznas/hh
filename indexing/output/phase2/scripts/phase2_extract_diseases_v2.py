#!/usr/bin/env python3
"""
Phase 2.1: Extract Disease/Condition Entities from Wills Eye Manual (v2)

Enhanced version that extracts clean disease names with:
- Proper synonym handling
- Clean entity names (no long DDx descriptions)
- Better pattern matching
- Hierarchical disease classification

Input: Phase 1 outputs (text blocks, lists, chapters)
Output: diseases.json with clean entity schema
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Paths
BASE_DIR = Path(__file__).parent
PHASE1_DIR = BASE_DIR / "output" / "phase1"
PHASE2_DIR = BASE_DIR / "output" / "phase2"

# Disease name patterns (suffix-based)
DISEASE_SUFFIXES = [
    r'\b(\w+itis)\b',       # -itis: keratitis, conjunctivitis, uveitis
    r'\b(\w+oma)\b',        # -oma: melanoma, glaucoma, lymphoma
    r'\b(\w+opathy)\b',     # -opathy: retinopathy, neuropathy
    r'\b(\w+trophy)\b',     # -trophy: dystrophy, atrophy
    r'\b(\w+osis)\b',       # -osis: keratosis, necrosis, thrombosis
    r'\b(\w+pathy)\b',      # -pathy: keratopathy
    r'\b(\w+plasia)\b',     # -plasia: hyperplasia, neoplasia
]

# Common disease terms (seed list)
KNOWN_DISEASES = {
    # Corneal
    'keratitis', 'keratopathy', 'corneal ulcer', 'corneal abrasion', 'corneal erosion',
    'corneal edema', 'corneal dystrophy', 'keratoconus', 'corneal infiltrate',
    'corneal perforation', 'corneal laceration', 'corneal foreign body',

    # Conjunctival/Scleral
    'conjunctivitis', 'episcleritis', 'scleritis', 'pterygium', 'pinguecula',
    'subconjunctival hemorrhage', 'conjunctival laceration',

    # Uveal
    'uveitis', 'iritis', 'iridocyclitis', 'choroiditis', 'panuveitis',
    'anterior uveitis', 'posterior uveitis', 'intermediate uveitis',

    # Retinal
    'retinopathy', 'retinal detachment', 'retinal tear', 'retinal break',
    'macular degeneration', 'macular edema', 'macular hole',
    'diabetic retinopathy', 'hypertensive retinopathy',
    'central retinal artery occlusion', 'central retinal vein occlusion',
    'vitreous hemorrhage', 'retinitis', 'chorioretinitis',

    # Glaucoma
    'glaucoma', 'angle-closure glaucoma', 'open-angle glaucoma',
    'acute glaucoma', 'chronic glaucoma', 'neovascular glaucoma',

    # Eyelid
    'blepharitis', 'chalazion', 'hordeolum', 'stye', 'ectropion', 'entropion',
    'blepharospasm', 'ptosis', 'trichiasis', 'distichiasis',

    # Orbital
    'orbital cellulitis', 'preseptal cellulitis', 'orbital fracture',
    'orbital hemorrhage', 'proptosis', 'enophthalmos',

    # Lens
    'cataract', 'aphakia', 'pseudophakia', 'lens dislocation',

    # Neuro-ophthalmic
    'optic neuritis', 'papillitis', 'papilledema', 'optic atrophy',
    'ischemic optic neuropathy', 'optic neuropathy',

    # Trauma
    'hyphema', 'hypopyon', 'chemical burn', 'thermal burn',
    'penetrating trauma', 'blunt trauma', 'globe rupture',

    # Tumors
    'melanoma', 'nevus', 'retinoblastoma', 'lymphoma',

    # Inflammatory
    'endophthalmitis', 'panophthalmitis', 'dacryocystitis', 'canaliculitis',

    # Other
    'dry eye', 'keratoconjunctivitis sicca', 'exposure keratopathy',
    'corneal neovascularization', 'band keratopathy',
}

# Trauma/emergency keywords for red flag detection
TRAUMA_KEYWORDS = {
    'chemical burn', 'alkali burn', 'acid burn', 'thermal burn',
    'penetrating trauma', 'penetrating injury', 'perforating injury',
    'globe rupture', 'ruptured globe', 'open globe',
    'intraocular foreign body', 'metallic foreign body',
    'orbital fracture', 'blowout fracture',
}

# Chapter-based severity mapping
CHAPTER_SEVERITY = {
    1: 'varies',     # Symptoms
    2: 'varies',     # Signs
    3: 'emergent',   # Trauma
    4: 'urgent',     # Cornea
    5: 'urgent',     # Conjunctiva/Sclera/Iris
    6: 'non-urgent', # Eyelid
    7: 'urgent',     # Orbit
    8: 'urgent',     # Pediatrics
    9: 'urgent',     # Glaucoma
    10: 'urgent',    # Neuro-ophthalmology
    11: 'emergent',  # Retina (many emergent conditions)
    12: 'urgent',    # Uveitis
    13: 'varies',    # General
    14: 'non-urgent',# Imaging
}


def normalize_name(name: str) -> str:
    """Normalize entity name."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    # Remove common prefixes/suffixes in long names
    name = re.sub(r'^(acute|chronic|bilateral|unilateral|primary|secondary)\s+', '', name)
    return name


def clean_disease_name(raw_name: str) -> str:
    """
    Extract clean disease name from DDx item.

    DDx items often have format: "Disease Name: description, details. See X.Y."
    We want just the disease name.
    """
    # Split on colon (disease name usually before colon)
    if ':' in raw_name:
        name = raw_name.split(':')[0].strip()
    else:
        # Take first sentence
        name = raw_name.split('.')[0].strip()

    # Clean up
    name = re.sub(r'\s+', ' ', name)

    # Remove "DDx" prefix if present
    name = re.sub(r'^ddx\s+', '', name, flags=re.IGNORECASE)

    # If still too long (>100 chars), take first clause
    if len(name) > 100:
        # Split on commas and take first part
        name = name.split(',')[0].strip()

    return name


def extract_diseases_from_ddx_lists(lists_data: List[Dict]) -> Dict[str, Dict]:
    """Extract disease entities from differential diagnosis lists."""
    diseases = {}
    disease_mentions = defaultdict(int)
    disease_chapters = defaultdict(set)
    disease_sections = defaultdict(set)

    ddx_lists = [lst for lst in lists_data if lst['list_type'] == 'differential_diagnosis']

    print(f"Processing {len(ddx_lists)} differential diagnosis lists...")

    for lst in ddx_lists:
        chapter = lst['chapter_number']
        section = lst['section']

        for item in lst['items']:
            # Clean the disease name
            raw_name = item.strip()
            if not raw_name or len(raw_name) < 3:
                continue

            clean_name = clean_disease_name(raw_name)
            normalized = normalize_name(clean_name)

            # Skip if too short or generic
            if len(normalized) < 3:
                continue

            generic_terms = ['unknown', 'other', 'various', 'multiple', 'see', 'refer']
            if any(term in normalized for term in generic_terms):
                continue

            # Track mentions and context
            disease_mentions[normalized] += 1
            disease_chapters[normalized].add(chapter)
            disease_sections[normalized].add(section)

    # Create disease entities
    entity_id = 1
    for disease_name, mention_count in disease_mentions.items():
        # Determine severity based on chapters
        chapters_list = sorted(disease_chapters[disease_name])
        primary_chapter = chapters_list[0]
        severity = CHAPTER_SEVERITY.get(primary_chapter, 'urgent')

        # Red flag if from Chapter 3 (Trauma) or matches trauma keywords
        red_flag = (3 in chapters_list) or any(kw in disease_name for kw in TRAUMA_KEYWORDS)

        # If from Retina chapter (11), check for emergency conditions
        if 11 in chapters_list:
            retina_emergencies = ['detachment', 'occlusion', 'tear', 'hemorrhage']
            if any(term in disease_name for term in retina_emergencies):
                severity = 'emergent'
                red_flag = True

        diseases[disease_name] = {
            'entity_id': f'disease_{entity_id:03d}',
            'name': disease_name.title(),
            'name_normalized': disease_name,
            'synonyms': [],
            'icd_10': None,
            'snomed_ct': None,
            'description': f'Disease entity extracted from differential diagnosis lists',
            'chapters': chapters_list,
            'sections': sorted(disease_sections[disease_name]),
            'severity': severity,
            'red_flag': red_flag,
            'from_differential_diagnosis': True,
            'from_section_heading': False,
            'mention_count': mention_count,
        }
        entity_id += 1

    return diseases


def extract_diseases_from_text_blocks(blocks_data: List[Dict], existing_diseases: Dict[str, Dict]) -> Dict[str, Dict]:
    """Extract additional diseases from text blocks using pattern matching."""
    diseases = dict(existing_diseases)  # Start with DDx diseases
    disease_mentions = defaultdict(int)
    disease_chapters = defaultdict(set)
    disease_sections = defaultdict(set)

    print(f"Processing {len(blocks_data)} text blocks for additional diseases...")

    # Start entity_id after existing diseases
    entity_id = len(diseases) + 1

    for block in blocks_data:
        text = block['text']
        chapter = block['chapter_number']
        section = block.get('section_path', ['Unknown'])[0] if block.get('section_path') else 'Unknown'

        # Extract using patterns
        extracted = set()

        # Pattern-based extraction
        for pattern in DISEASE_SUFFIXES:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                normalized = normalize_name(match)
                if len(normalized) > 3:
                    extracted.add(normalized)

        # Known disease matching
        text_lower = text.lower()
        for known_disease in KNOWN_DISEASES:
            if known_disease in text_lower:
                extracted.add(known_disease)

        # Track mentions
        for disease_name in extracted:
            if disease_name in diseases:
                # Update existing disease
                diseases[disease_name]['mention_count'] += 1
                diseases[disease_name]['chapters'] = sorted(set(diseases[disease_name]['chapters'] + [chapter]))
            else:
                # New disease not in DDx lists
                disease_mentions[disease_name] += 1
                disease_chapters[disease_name].add(chapter)
                disease_sections[disease_name].add(section)

    # Add new diseases with sufficient mentions (≥2 mentions)
    for disease_name, mention_count in disease_mentions.items():
        if mention_count >= 2:
            chapters_list = sorted(disease_chapters[disease_name])
            primary_chapter = chapters_list[0]
            severity = CHAPTER_SEVERITY.get(primary_chapter, 'urgent')

            red_flag = (3 in chapters_list) or any(kw in disease_name for kw in TRAUMA_KEYWORDS)

            diseases[disease_name] = {
                'entity_id': f'disease_{entity_id:03d}',
                'name': disease_name.title(),
                'name_normalized': disease_name,
                'synonyms': [],
                'icd_10': None,
                'snomed_ct': None,
                'description': f'Disease entity extracted from text analysis',
                'chapters': chapters_list,
                'sections': sorted(disease_sections[disease_name]),
                'severity': severity,
                'red_flag': red_flag,
                'from_differential_diagnosis': False,
                'from_section_heading': False,
                'mention_count': mention_count,
            }
            entity_id += 1

    return diseases


def add_synonyms(diseases: Dict[str, Dict]) -> Dict[str, Dict]:
    """Add common synonyms to disease entities."""

    synonym_map = {
        'stye': ['hordeolum'],
        'hordeolum': ['stye'],
        'pink eye': ['conjunctivitis'],
        'keratoconjunctivitis sicca': ['dry eye', 'dry eye syndrome'],
        'dry eye': ['keratoconjunctivitis sicca'],
        'corneal abrasion': ['corneal scratch', 'scratched cornea'],
        'hyphema': ['blood in anterior chamber'],
        'hypopyon': ['pus in anterior chamber'],
        'chalazion': ['meibomian cyst'],
        'pterygium': ['surfer\'s eye'],
        'central retinal artery occlusion': ['crao'],
        'central retinal vein occlusion': ['crvo'],
        'age-related macular degeneration': ['amd', 'armd', 'macular degeneration'],
        'macular degeneration': ['amd', 'age-related macular degeneration'],
    }

    for disease_name, disease_data in diseases.items():
        if disease_name in synonym_map:
            disease_data['synonyms'] = synonym_map[disease_name]

    return diseases


def main():
    """Main extraction pipeline."""
    print("=" * 60)
    print("Phase 2.1: Disease Entity Extraction (v2)")
    print("=" * 60)

    # Create output directory
    PHASE2_DIR.mkdir(parents=True, exist_ok=True)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(PHASE1_DIR / "wills_eye_lists.json", 'r', encoding='utf-8') as f:
        lists_data = json.load(f)

    with open(PHASE1_DIR / "wills_eye_text_blocks.json", 'r', encoding='utf-8') as f:
        blocks_data = json.load(f)

    print(f"Loaded {len(lists_data)} lists and {len(blocks_data)} text blocks")

    # Step 1: Extract from DDx lists (highest confidence)
    print("\n" + "="*60)
    print("Step 1: Extracting from differential diagnosis lists...")
    print("="*60)
    diseases = extract_diseases_from_ddx_lists(lists_data)
    print(f"Extracted {len(diseases)} diseases from DDx lists")

    # Step 2: Extract from text blocks (pattern matching)
    print("\n" + "="*60)
    print("Step 2: Extracting from text blocks...")
    print("="*60)
    diseases = extract_diseases_from_text_blocks(blocks_data, diseases)
    print(f"Total diseases after text analysis: {len(diseases)}")

    # Step 3: Add synonyms
    print("\n" + "="*60)
    print("Step 3: Adding synonyms...")
    print("="*60)
    diseases = add_synonyms(diseases)
    diseases_with_synonyms = sum(1 for d in diseases.values() if d['synonyms'])
    print(f"Added synonyms to {diseases_with_synonyms} diseases")

    # Convert to list and sort by entity_id
    diseases_list = sorted(diseases.values(), key=lambda x: x['entity_id'])

    # Generate statistics
    print("\n" + "="*60)
    print("Statistics:")
    print("="*60)
    print(f"Total disease entities: {len(diseases_list)}")

    severity_counts = defaultdict(int)
    for disease in diseases_list:
        severity_counts[disease['severity']] += 1

    print(f"\nSeverity distribution:")
    for severity, count in sorted(severity_counts.items()):
        print(f"  {severity}: {count}")

    red_flag_count = sum(1 for d in diseases_list if d['red_flag'])
    print(f"\nRed flag conditions: {red_flag_count}")

    from_ddx = sum(1 for d in diseases_list if d['from_differential_diagnosis'])
    print(f"From differential diagnosis lists: {from_ddx}")

    # Save diseases.json
    output_file = PHASE2_DIR / "diseases.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(diseases_list, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(diseases_list)} diseases to {output_file}")

    # Save report
    report = {
        'phase': '2.1 - Disease Entity Extraction (v2)',
        'total_entities': len(diseases_list),
        'severity_distribution': dict(severity_counts),
        'red_flag_count': red_flag_count,
        'from_differential_diagnosis': from_ddx,
        'with_synonyms': diseases_with_synonyms,
        'top_diseases_by_mentions': [
            {'name': d['name'], 'mentions': d['mention_count']}
            for d in sorted(diseases_list, key=lambda x: x['mention_count'], reverse=True)[:15]
        ]
    }

    report_file = PHASE2_DIR / "phase2_1_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Saved report to {report_file}")
    print("\n" + "="*60)
    print("Phase 2.1 Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
