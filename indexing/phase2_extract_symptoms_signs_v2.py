#!/usr/bin/env python3
"""
Phase 2.2: Extract Symptom and Sign Entities from Wills Eye Manual (v2)

Enhanced version that extracts comprehensive symptoms and signs from:
- Chapter 1 (Symptoms) - Patient-reported
- Chapter 2 (Signs) - Clinician-observed
- Differential diagnosis structures
- Text blocks with symptom/sign keywords

Output: symptoms.json, signs.json
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

# Known symptom keywords (patient-reported, subjective)
SYMPTOM_KEYWORDS = {
    # Vision changes
    'blurred vision', 'blurry vision', 'vision loss', 'decreased vision',
    'loss of vision', 'reduced vision', 'dim vision', 'foggy vision',
    'distorted vision', 'double vision', 'diplopia',
    'sudden vision loss', 'gradual vision loss',

    # Pain and discomfort
    'pain', 'eye pain', 'ocular pain', 'ache', 'discomfort',
    'burning', 'stinging', 'foreign body sensation',
    'gritty feeling', 'sandy feeling', 'irritation',

    # Light sensitivity
    'photophobia', 'light sensitivity', 'sensitivity to light',
    'glare', 'halos', 'glare sensitivity',

    # Visual phenomena
    'floaters', 'spots', 'flashes', 'flashing lights',
    'seeing spots', 'seeing floaters', 'photopsia',
    'scotoma', 'blind spot', 'dark spot',
    'shadows', 'curtain', 'veil',

    # Secretions
    'discharge', 'tearing', 'watering', 'excessive tearing',
    'epiphora', 'crusting', 'mattering',
    'mucus discharge', 'purulent discharge',

    # Itching
    'itching', 'itchy eyes', 'pruritus',

    # Dryness
    'dryness', 'dry eyes', 'dry eye sensation',

    # Metamorphopsia
    'distortion', 'metamorphopsia', 'wavy lines',
    'bent lines', 'crooked lines',

    # Nyctalopia
    'night blindness', 'nyctalopia', 'difficulty seeing at night',

    # Color vision
    'color vision changes', 'color distortion',

    # Headache
    'headache', 'periorbital pain', 'brow ache',
}

# Known sign keywords (clinician-observed, objective)
SIGN_KEYWORDS = {
    # Redness
    'redness', 'red eye', 'injection', 'hyperemia',
    'conjunctival injection', 'ciliary injection',
    'circumcorneal injection',

    # Swelling/Edema
    'swelling', 'edema', 'chemosis', 'lid swelling',
    'periorbital swelling', 'eyelid edema',
    'corneal edema', 'macular edema',

    # Opacity
    'opacity', 'corneal opacity', 'lens opacity',
    'hazy cornea', 'cloudy cornea',

    # Hemorrhage
    'hemorrhage', 'bleeding', 'blood',
    'subconjunctival hemorrhage', 'vitreous hemorrhage',
    'retinal hemorrhage', 'hyphema',

    # Discharge/Secretions
    'exudate', 'hypopyon', 'pus',

    # Pupil abnormalities
    'abnormal pupil', 'irregular pupil', 'dilated pupil',
    'constricted pupil', 'afferent pupillary defect',
    'relative afferent pupillary defect', 'rapd',
    'anisocoria', 'mydriasis', 'miosis',

    # Anterior chamber
    'anterior chamber cell', 'anterior chamber flare',
    'shallow anterior chamber', 'flat anterior chamber',

    # Corneal findings
    'corneal infiltrate', 'corneal ulcer', 'corneal defect',
    'epithelial defect', 'corneal staining', 'fluorescein staining',
    'dendrite', 'corneal dendrite',

    # Eyelid findings
    'ptosis', 'lid lag', 'ectropion', 'entropion',
    'blepharospasm', 'lagophthalmos',

    # Proptosis
    'proptosis', 'exophthalmos', 'enophthalmos',

    # Nystagmus
    'nystagmus', 'oscillopsia',

    # Optic disc
    'optic disc abnormality', 'disc swelling', 'papilledema',
    'optic disc pallor', 'disc hemorrhage',
    'cup-to-disc ratio abnormality',

    # Retinal findings
    'retinal detachment', 'retinal tear', 'retinal whitening',
    'cherry red spot', 'cotton wool spots',
    'hard exudates', 'soft exudates', 'drusen',

    # Vitreous findings
    'vitreous cell', 'vitreous haze', 'vitreous opacities',

    # Intraocular pressure
    'elevated iop', 'high eye pressure', 'increased intraocular pressure',
    'low iop', 'hypotony',

    # Neovascularization
    'neovascularization', 'new vessels', 'corneal neovascularization',
    'iris neovascularization', 'retinal neovascularization',
}


def normalize_name(name: str) -> str:
    """Normalize entity name."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    return name


def extract_from_chapter_headings(blocks_data: List[Dict], chapter_num: int, entity_type: str) -> Dict[str, Dict]:
    """Extract symptoms/signs from chapter headings."""
    entities = {}
    entity_id = 1

    # Filter blocks from the specific chapter
    chapter_blocks = [b for b in blocks_data if b['chapter_number'] == chapter_num]

    print(f"Processing {len(chapter_blocks)} blocks from Chapter {chapter_num}...")

    # Track sections (section headings are the symptom/sign names)
    seen_sections = set()

    for block in chapter_blocks:
        section_path = block.get('section_path', [])
        if not section_path:
            continue

        # The first level section is usually the symptom/sign name
        section_name = section_path[0]

        if section_name in seen_sections:
            continue

        seen_sections.add(section_name)

        # Skip generic section names
        generic = ['differential diagnosis', 'introduction', 'overview',
                   'general', 'workup', 'etiology', 'management']
        if any(g in section_name.lower() for g in generic):
            continue

        # This is likely a symptom/sign
        normalized = normalize_name(section_name)

        if len(normalized) < 3:
            continue

        entities[normalized] = {
            'entity_id': f'{entity_type}_{entity_id:03d}',
            'name': section_name.title(),
            'name_normalized': normalized,
            'type': entity_type,
            'category': 'ocular',
            'red_flag': False,
            'chapter': chapter_num,
            'section': section_name,
            'associated_conditions': [],
            'variations': [],
            'mention_count': 1,
        }
        entity_id += 1

    return entities


def extract_from_ddx_structures(ddx_data: List[Dict], entity_type: str) -> Dict[str, Dict]:
    """Extract symptoms/signs from differential diagnosis structures."""
    entities = {}

    print(f"Processing {len(ddx_data)} differential diagnosis structures...")

    for ddx in ddx_data:
        presenting_complaint = ddx.get('presenting_complaint', '')

        if not presenting_complaint:
            continue

        normalized = normalize_name(presenting_complaint)

        # Skip if too generic or already processed
        if len(normalized) < 3:
            continue

        # Extract associated conditions
        associated = []
        for diff_diagnosis in ddx.get('differential_diagnoses', []):
            disease_name = diff_diagnosis.get('disease', '')
            if disease_name:
                # Clean disease name (remove DDx descriptions)
                if ':' in disease_name:
                    disease_name = disease_name.split(':')[0].strip()
                associated.append(disease_name)

        # Determine chapter (from first condition if available)
        chapter_match = re.search(r'Chapter (\d+)', str(ddx))
        chapter = int(chapter_match.group(1)) if chapter_match else None

        # Determine if symptom or sign based on keywords
        is_symptom = any(kw in normalized for kw in SYMPTOM_KEYWORDS)
        is_sign = any(kw in normalized for kw in SIGN_KEYWORDS)

        # If unclear, use chapter number
        if not is_symptom and not is_sign:
            if chapter == 1:
                is_symptom = True
            elif chapter == 2:
                is_sign = True
            else:
                continue  # Skip if can't determine

        determined_type = 'symptom' if is_symptom else 'sign'

        if determined_type != entity_type:
            continue

        entities[normalized] = {
            'entity_id': f'{entity_type}_{len(entities)+1:03d}',
            'name': presenting_complaint.title(),
            'name_normalized': normalized,
            'type': entity_type,
            'category': 'ocular',
            'red_flag': False,
            'chapter': chapter,
            'section': presenting_complaint,
            'associated_conditions': associated[:10],  # Limit to top 10
            'variations': [],
            'mention_count': 1,
        }

    return entities


def extract_from_text_with_keywords(blocks_data: List[Dict], keywords: Set[str], entity_type: str) -> Dict[str, Dict]:
    """Extract symptoms/signs from text blocks using keyword matching."""
    entities = {}
    entity_mentions = defaultdict(int)
    entity_chapters = defaultdict(set)

    print(f"Scanning {len(blocks_data)} text blocks for {entity_type} keywords...")

    for block in blocks_data:
        text = block['text'].lower()
        chapter = block['chapter_number']

        for keyword in keywords:
            if keyword in text:
                normalized = normalize_name(keyword)
                entity_mentions[normalized] += 1
                entity_chapters[normalized].add(chapter)

    # Create entities for keywords with sufficient mentions (≥3)
    entity_id = 1
    for keyword, mention_count in entity_mentions.items():
        if mention_count >= 3:
            chapters = sorted(entity_chapters[keyword])

            # Check if it's a red flag (e.g., sudden vision loss, chemical injury)
            red_flag_terms = ['sudden vision loss', 'chemical', 'penetrating', 'trauma']
            is_red_flag = any(term in keyword for term in red_flag_terms)

            entities[keyword] = {
                'entity_id': f'{entity_type}_{entity_id:03d}',
                'name': keyword.title(),
                'name_normalized': keyword,
                'type': entity_type,
                'category': 'ocular',
                'red_flag': is_red_flag,
                'chapter': chapters[0],  # Primary chapter
                'chapters': chapters,
                'section': None,
                'associated_conditions': [],
                'variations': [],
                'mention_count': mention_count,
            }
            entity_id += 1

    return entities


def merge_entities(entity_dicts: List[Dict[str, Dict]]) -> List[Dict]:
    """Merge entities from multiple sources, avoiding duplicates."""
    merged = {}

    for entity_dict in entity_dicts:
        for key, entity in entity_dict.items():
            if key not in merged:
                merged[key] = entity
            else:
                # Entity exists, merge information
                existing = merged[key]

                # Update mention count
                existing['mention_count'] += entity.get('mention_count', 1)

                # Merge associated conditions
                if entity.get('associated_conditions'):
                    existing_conds = set(existing.get('associated_conditions', []))
                    new_conds = set(entity['associated_conditions'])
                    existing['associated_conditions'] = sorted(existing_conds | new_conds)[:15]

                # Merge chapters
                if entity.get('chapters'):
                    existing_chapters = set(existing.get('chapters', [existing.get('chapter', 0)]))
                    new_chapters = set(entity['chapters'])
                    merged_chapters = sorted(existing_chapters | new_chapters)
                    existing['chapters'] = merged_chapters
                    existing['chapter'] = merged_chapters[0]

                # Update red flag if any source marks it
                if entity.get('red_flag'):
                    existing['red_flag'] = True

    # Convert to list and sort by entity_id
    return sorted(merged.values(), key=lambda x: x['entity_id'])


def main():
    """Main extraction pipeline."""
    print("=" * 60)
    print("Phase 2.2: Symptom & Sign Entity Extraction (v2)")
    print("=" * 60)

    # Create output directory
    PHASE2_DIR.mkdir(parents=True, exist_ok=True)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", 'r', encoding='utf-8') as f:
        blocks_data = json.load(f)

    with open(PHASE1_DIR / "differential_diagnoses.json", 'r', encoding='utf-8') as f:
        ddx_file = json.load(f)
        # Extract the actual list from the file structure
        ddx_data = ddx_file.get('differential_diagnoses', [])

    print(f"Loaded {len(blocks_data)} text blocks and {len(ddx_data)} DDx structures")

    # Extract Symptoms (Chapter 1)
    print("\n" + "="*60)
    print("Extracting SYMPTOMS...")
    print("="*60)

    symptoms_from_headings = extract_from_chapter_headings(blocks_data, 1, 'symptom')
    print(f"From Chapter 1 headings: {len(symptoms_from_headings)}")

    symptoms_from_ddx = extract_from_ddx_structures(ddx_data, 'symptom')
    print(f"From DDx structures: {len(symptoms_from_ddx)}")

    symptoms_from_keywords = extract_from_text_with_keywords(blocks_data, SYMPTOM_KEYWORDS, 'symptom')
    print(f"From keyword matching: {len(symptoms_from_keywords)}")

    symptoms_list = merge_entities([symptoms_from_headings, symptoms_from_ddx, symptoms_from_keywords])
    print(f"\nTotal unique symptoms: {len(symptoms_list)}")

    # Extract Signs (Chapter 2)
    print("\n" + "="*60)
    print("Extracting SIGNS...")
    print("="*60)

    signs_from_headings = extract_from_chapter_headings(blocks_data, 2, 'sign')
    print(f"From Chapter 2 headings: {len(signs_from_headings)}")

    signs_from_ddx = extract_from_ddx_structures(ddx_data, 'sign')
    print(f"From DDx structures: {len(signs_from_ddx)}")

    signs_from_keywords = extract_from_text_with_keywords(blocks_data, SIGN_KEYWORDS, 'sign')
    print(f"From keyword matching: {len(signs_from_keywords)}")

    signs_list = merge_entities([signs_from_headings, signs_from_ddx, signs_from_keywords])
    print(f"\nTotal unique signs: {len(signs_list)}")

    # Save symptoms
    symptoms_file = PHASE2_DIR / "symptoms.json"
    with open(symptoms_file, 'w', encoding='utf-8') as f:
        json.dump(symptoms_list, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Saved {len(symptoms_list)} symptoms to {symptoms_file}")

    # Save signs
    signs_file = PHASE2_DIR / "signs.json"
    with open(signs_file, 'w', encoding='utf-8') as f:
        json.dump(signs_list, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {len(signs_list)} signs to {signs_file}")

    # Generate report
    report = {
        'phase': '2.2 - Symptom & Sign Entity Extraction (v2)',
        'symptoms': {
            'total': len(symptoms_list),
            'red_flag_count': sum(1 for s in symptoms_list if s.get('red_flag')),
            'top_by_mentions': [
                {'name': s['name'], 'mentions': s['mention_count']}
                for s in sorted(symptoms_list, key=lambda x: x['mention_count'], reverse=True)[:10]
            ]
        },
        'signs': {
            'total': len(signs_list),
            'red_flag_count': sum(1 for s in signs_list if s.get('red_flag')),
            'top_by_mentions': [
                {'name': s['name'], 'mentions': s['mention_count']}
                for s in sorted(signs_list, key=lambda x: x['mention_count'], reverse=True)[:10]
            ]
        }
    }

    report_file = PHASE2_DIR / "phase2_2_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"[OK] Saved report to {report_file}")

    print("\n" + "="*60)
    print("Phase 2.2 Complete!")
    print("="*60)
    print(f"Symptoms: {len(symptoms_list)}")
    print(f"Signs: {len(signs_list)}")
    print(f"Total: {len(symptoms_list) + len(signs_list)}")


if __name__ == '__main__':
    main()
