#!/usr/bin/env python3
"""
Phase 2.4: Extract Diagnostic Test/Imaging Entities from Wills Eye Manual

Extracts diagnostic tests and imaging modalities from:
- Chapter 14 (Imaging Modalities)
- Examination lists throughout the manual
- Text blocks with test/imaging keywords

Output: diagnostic_tests.json
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

# Known diagnostic tests and imaging modalities
KNOWN_TESTS = {
    # Imaging
    'optical coherence tomography', 'oct', 'oct angiography', 'octa',
    'fluorescein angiography', 'fa', 'fundus fluorescein angiography',
    'indocyanine green angiography', 'icg', 'icg angiography',
    'fundus photography', 'fundus autofluorescence', 'faf',
    'ultrasound', 'b-scan', 'b-scan ultrasound', 'a-scan', 'a-scan ultrasound',
    'ultrasonography', 'ultrasound biomicroscopy', 'ubm',
    'ct scan', 'computed tomography', 'orbital ct', 'head ct',
    'mri', 'magnetic resonance imaging', 'orbital mri', 'brain mri',
    'x-ray', 'orbital x-ray',

    # Visual field testing
    'visual field', 'visual field testing', 'perimetry',
    'automated perimetry', 'humphrey visual field',
    'goldmann perimetry', 'confrontation visual fields',

    # Electrophysiology
    'erg', 'electroretinography', 'electroretinogram',
    'vep', 'visual evoked potential', 'visual evoked response',
    'eog', 'electrooculography', 'electrooculogram',
    'multifocal erg', 'mferg',

    # Laboratory tests
    'culture', 'bacterial culture', 'fungal culture', 'viral culture',
    'gram stain', 'giemsa stain', 'koh prep',
    'pcr', 'polymerase chain reaction',
    'serology', 'blood test', 'cbc', 'complete blood count',
    'esr', 'erythrocyte sedimentation rate',
    'ana', 'antinuclear antibody',
    'anca', 'antineutrophil cytoplasmic antibody',
    'ace level', 'angiotensin converting enzyme',
    'lysozyme', 'hla typing', 'hla-b27',
    'rpr', 'rapid plasma reagin', 'vdrl', 'fta-abs',

    # Tonometry
    'tonometry', 'applanation tonometry', 'goldmann tonometry',
    'tono-pen', 'icare tonometry', 'pneumotonometry',
    'intraocular pressure measurement', 'iop measurement',

    # Gonioscopy
    'gonioscopy', 'angle examination',

    # Biometry
    'biometry', 'iol calculation', 'keratometry',
    'corneal topography', 'topography', 'pentacam',
    'pachymetry', 'corneal pachymetry',
    'specular microscopy', 'endothelial cell count',

    # Staining
    'fluorescein staining', 'rose bengal staining',
    'lissamine green staining',

    # Tear film testing
    'schirmer test', 'tear breakup time', 'tbut',
    'tear osmolarity',

    # Color vision
    'ishihara test', 'color vision testing',
    'farnsworth d-15', 'hardy-rand-rittler',

    # Amsler grid
    'amsler grid',

    # Miscellaneous
    'slit lamp examination', 'biomicroscopy',
    'fundoscopy', 'ophthalmoscopy', 'indirect ophthalmoscopy',
    'direct ophthalmoscopy',
    'exophthalmometry', 'hertel exophthalmometry',
}


def normalize_name(name: str) -> str:
    """Normalize entity name."""
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    return name


def extract_from_chapter_14(blocks_data: List[Dict]) -> Dict[str, Dict]:
    """Extract diagnostic tests from Chapter 14 (Imaging Modalities)."""
    tests = {}
    test_mentions = defaultdict(int)
    test_descriptions = defaultdict(str)

    # Filter Chapter 14 blocks
    ch14_blocks = [b for b in blocks_data if b['chapter_number'] == 14]

    print(f"Processing {len(ch14_blocks)} blocks from Chapter 14...")

    # Extract section names as test names
    seen_sections = set()

    for block in ch14_blocks:
        section_path = block.get('section_path', [])
        if not section_path:
            continue

        section_name = section_path[0]

        if section_name in seen_sections:
            continue

        seen_sections.add(section_name)

        # Skip generic sections
        generic = ['introduction', 'overview', 'general', 'imaging modalities']
        if any(g in section_name.lower() for g in generic):
            continue

        normalized = normalize_name(section_name)

        # Get description from first text block of this section
        description = block['text'][:200] if len(block['text']) >= 200 else block['text']

        tests[normalized] = {
            'entity_id': f'test_{len(tests)+1:03d}',
            'name': section_name.title(),
            'name_normalized': normalized,
            'type': 'imaging',
            'category': 'diagnostic',
            'chapter': 14,
            'description': description,
            'mention_count': 1,
        }

    return tests


def extract_from_examination_lists(lists_data: List[Dict]) -> Dict[str, Dict]:
    """Extract diagnostic tests from examination lists."""
    tests = {}
    test_mentions = defaultdict(int)
    test_chapters = defaultdict(set)

    exam_lists = [lst for lst in lists_data if lst['list_type'] == 'examination']

    print(f"Processing {len(exam_lists)} examination lists...")

    for lst in exam_lists:
        chapter = lst['chapter_number']

        for item in lst['items']:
            item_lower = item.lower()

            # Check against known tests
            for known_test in KNOWN_TESTS:
                if known_test in item_lower:
                    normalized = normalize_name(known_test)
                    test_mentions[normalized] += 1
                    test_chapters[normalized].add(chapter)

    # Create entities
    entity_id = 100  # Start at 100 to avoid conflicts with Ch14
    for test_name, mention_count in test_mentions.items():
        if mention_count >= 1:
            tests[test_name] = {
                'entity_id': f'test_{entity_id:03d}',
                'name': test_name.title(),
                'name_normalized': test_name,
                'type': 'examination',
                'category': 'diagnostic',
                'chapters': sorted(test_chapters[test_name]),
                'description': f'Diagnostic test extracted from examination lists',
                'mention_count': mention_count,
            }
            entity_id += 1

    return tests


def extract_from_text_blocks(blocks_data: List[Dict]) -> Dict[str, Dict]:
    """Extract diagnostic tests from text blocks using keyword matching."""
    tests = {}
    test_mentions = defaultdict(int)
    test_chapters = defaultdict(set)

    print(f"Scanning {len(blocks_data)} text blocks for diagnostic test keywords...")

    for block in blocks_data:
        text = block['text'].lower()
        chapter = block['chapter_number']

        for known_test in KNOWN_TESTS:
            if known_test in text:
                normalized = normalize_name(known_test)
                test_mentions[normalized] += 1
                test_chapters[normalized].add(chapter)

    # Create entities for tests with sufficient mentions (≥5)
    entity_id = 200  # Start at 200
    for test_name, mention_count in test_mentions.items():
        if mention_count >= 5:
            chapters = sorted(test_chapters[test_name])

            # Determine type based on test name
            if any(term in test_name for term in ['oct', 'angiography', 'ultrasound', 'ct', 'mri', 'x-ray', 'imaging', 'photography']):
                test_type = 'imaging'
            elif any(term in test_name for term in ['culture', 'stain', 'pcr', 'serology', 'blood', 'lab']):
                test_type = 'laboratory'
            elif any(term in test_name for term in ['visual field', 'perimetry', 'erg', 'vep', 'eog']):
                test_type = 'functional'
            else:
                test_type = 'examination'

            tests[test_name] = {
                'entity_id': f'test_{entity_id:03d}',
                'name': test_name.title(),
                'name_normalized': test_name,
                'type': test_type,
                'category': 'diagnostic',
                'chapters': chapters,
                'description': f'Diagnostic test extracted from text analysis',
                'mention_count': mention_count,
            }
            entity_id += 1

    return tests


def merge_tests(test_dicts: List[Dict[str, Dict]]) -> List[Dict]:
    """Merge tests from multiple sources, avoiding duplicates."""
    merged = {}

    for test_dict in test_dicts:
        for key, test in test_dict.items():
            if key not in merged:
                merged[key] = test
            else:
                # Merge information
                existing = merged[key]
                existing['mention_count'] += test.get('mention_count', 1)

                # Merge chapters if present
                if 'chapters' in test:
                    existing_chapters = set(existing.get('chapters', [existing.get('chapter', 0)]))
                    new_chapters = set(test['chapters'])
                    existing['chapters'] = sorted(existing_chapters | new_chapters)

    # Convert to list and renumber entity IDs
    tests_list = sorted(merged.values(), key=lambda x: (x['type'], x['name_normalized']))

    for idx, test in enumerate(tests_list, start=1):
        test['entity_id'] = f'test_{idx:03d}'

    return tests_list


def main():
    """Main extraction pipeline."""
    print("=" * 60)
    print("Phase 2.4: Diagnostic Test/Imaging Entity Extraction")
    print("=" * 60)

    # Create output directory
    PHASE2_DIR.mkdir(parents=True, exist_ok=True)

    # Load Phase 1 data
    print("\nLoading Phase 1 data...")
    with open(PHASE1_DIR / "wills_eye_text_blocks.json", 'r', encoding='utf-8') as f:
        blocks_data = json.load(f)

    with open(PHASE1_DIR / "wills_eye_lists.json", 'r', encoding='utf-8') as f:
        lists_data = json.load(f)

    print(f"Loaded {len(blocks_data)} text blocks and {len(lists_data)} lists")

    # Step 1: Extract from Chapter 14
    print("\n" + "="*60)
    print("Step 1: Extracting from Chapter 14 (Imaging Modalities)...")
    print("="*60)
    ch14_tests = extract_from_chapter_14(blocks_data)
    print(f"Extracted {len(ch14_tests)} imaging modalities")

    # Step 2: Extract from examination lists
    print("\n" + "="*60)
    print("Step 2: Extracting from examination lists...")
    print("="*60)
    exam_tests = extract_from_examination_lists(lists_data)
    print(f"Extracted {len(exam_tests)} tests from examination lists")

    # Step 3: Extract from text blocks
    print("\n" + "="*60)
    print("Step 3: Extracting from text blocks...")
    print("="*60)
    text_tests = extract_from_text_blocks(blocks_data)
    print(f"Extracted {len(text_tests)} tests from text analysis")

    # Merge all
    print("\n" + "="*60)
    print("Merging diagnostic tests...")
    print("="*60)
    tests_list = merge_tests([ch14_tests, exam_tests, text_tests])
    print(f"Total unique diagnostic tests: {len(tests_list)}")

    # Generate statistics
    print("\n" + "="*60)
    print("Statistics:")
    print("="*60)

    type_counts = defaultdict(int)
    for test in tests_list:
        type_counts[test['type']] += 1

    print(f"Total diagnostic test entities: {len(tests_list)}")
    print(f"\nType distribution:")
    for test_type, count in sorted(type_counts.items()):
        print(f"  {test_type}: {count}")

    # Save diagnostic_tests.json
    output_file = PHASE2_DIR / "diagnostic_tests.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tests_list, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved {len(tests_list)} diagnostic tests to {output_file}")

    # Save report
    report = {
        'phase': '2.4 - Diagnostic Test/Imaging Entity Extraction',
        'total_entities': len(tests_list),
        'type_distribution': dict(type_counts),
        'top_by_mentions': [
            {'name': t['name'], 'type': t['type'], 'mentions': t['mention_count']}
            for t in sorted(tests_list, key=lambda x: x['mention_count'], reverse=True)[:15]
        ]
    }

    report_file = PHASE2_DIR / "phase2_4_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Saved report to {report_file}")

    print("\n" + "="*60)
    print("Phase 2.4 Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
