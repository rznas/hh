#!/usr/bin/env python3
"""
Phase 1.3 Subtask: Create Specialized Differential Diagnosis Structures

Processes differential diagnosis lists to create structured JSON for GraphRAG.
Focuses on symptom-based DDx (Chapter 1) and sign-based DDx (Chapter 2).
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def create_ddx_structure_from_lists(lists_data: List[Dict]) -> Dict[str, Any]:
    """
    Create structured differential diagnosis mapping.

    Returns a dictionary mapping symptoms/signs to their differential diagnoses.
    """
    # Separate by chapter and list type
    ddx_lists = [lst for lst in lists_data if lst['list_type'] == 'differential_diagnosis']

    # Organize by chapter
    by_chapter = {}
    for lst in ddx_lists:
        ch_num = lst['chapter_number']
        if ch_num not in by_chapter:
            by_chapter[ch_num] = []
        by_chapter[ch_num].append(lst)

    # Create structured output
    differential_diagnoses = []

    for lst in ddx_lists:
        # Extract presenting complaint from section heading
        presenting_complaint = lst['section']
        chapter_num = lst['chapter_number']
        chapter_title = lst['chapter_title']

        # Classify as symptom-based or sign-based
        if chapter_num == 1:
            complaint_type = 'symptom'
        elif chapter_num == 2:
            complaint_type = 'sign'
        else:
            complaint_type = 'condition_specific'

        # Create differential diagnosis entry
        ddx_entry = {
            'id': lst['list_id'],
            'presenting_complaint': presenting_complaint,
            'complaint_type': complaint_type,
            'chapter_number': chapter_num,
            'chapter_title': chapter_title,
            'differential_diagnoses': [
                {
                    'rank': idx + 1,
                    'disease': disease.strip(),
                    'source_section': presenting_complaint
                }
                for idx, disease in enumerate(lst['items'])
            ],
            'total_differentials': len(lst['items'])
        }

        differential_diagnoses.append(ddx_entry)

    # Create summary statistics
    by_type = {}
    for ddx in differential_diagnoses:
        complaint_type = ddx['complaint_type']
        by_type[complaint_type] = by_type.get(complaint_type, 0) + 1

    output = {
        'metadata': {
            'total_differential_lists': len(differential_diagnoses),
            'by_type': by_type,
            'symptom_based_ddx': by_type.get('symptom', 0),
            'sign_based_ddx': by_type.get('sign', 0),
            'condition_specific_ddx': by_type.get('condition_specific', 0)
        },
        'differential_diagnoses': differential_diagnoses
    }

    return output

def main():
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / "indexing" / "output" / "phase1" / "wills_eye_lists.json"
    output_dir = base_dir / "indexing" / "output" / "phase1"

    print("=" * 60)
    print("Phase 1.3 Subtask: Create DDx Structures")
    print("=" * 60)

    # Load lists
    print(f"\nLoading: {input_file.name}")
    with open(input_file, encoding='utf-8') as f:
        lists_data = json.load(f)

    print(f"Total lists: {len(lists_data)}")

    # Create differential diagnosis structures
    print("\nCreating differential diagnosis structures...")
    ddx_output = create_ddx_structure_from_lists(lists_data)

    # Save output
    output_file = output_dir / "differential_diagnoses.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ddx_output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved: {output_file.name}")
    print(f"\nStatistics:")
    print(f"  Total differential diagnosis lists: {ddx_output['metadata']['total_differential_lists']}")
    print(f"  Symptom-based DDx: {ddx_output['metadata']['symptom_based_ddx']}")
    print(f"  Sign-based DDx: {ddx_output['metadata']['sign_based_ddx']}")
    print(f"  Condition-specific DDx: {ddx_output['metadata']['condition_specific_ddx']}")

    # Show sample from Chapter 1 and 2
    print(f"\nSample entries:")
    for ddx in ddx_output['differential_diagnoses'][:3]:
        print(f"  - {ddx['presenting_complaint']} ({ddx['complaint_type']}): {ddx['total_differentials']} differentials")

    print("\n" + "=" * 60)
    print("DDx Structure Creation Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
