#!/usr/bin/env python3
"""Phase 1 Validation - Compact Report Generator"""

import json
import sys
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def validate_phase1():
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "indexing" / "output" / "phase1"

    print("=" * 60)
    print("Phase 1 Validation")
    print("=" * 60)

    # Load all outputs
    with open(output_dir / "wills_eye_chapters_structured.json", encoding='utf-8') as f:
        chapters = json.load(f)

    with open(output_dir / "wills_eye_text_blocks.json", encoding='utf-8') as f:
        blocks = json.load(f)

    with open(output_dir / "wills_eye_lists.json", encoding='utf-8') as f:
        lists = json.load(f)

    with open(output_dir / "wills_eye_tables.json", encoding='utf-8') as f:
        tables = json.load(f)

    with open(output_dir / "differential_diagnoses.json", encoding='utf-8') as f:
        ddx = json.load(f)

    # Validate
    checks = []

    # Chapter completeness
    checks.append(("Chapters extracted", len(chapters) == 14, f"{len(chapters)}/14"))

    # Text blocks quality
    empty_blocks = sum(1 for b in blocks if len(b.get('text', '')) < 20)
    checks.append(("Text blocks valid", empty_blocks == 0, f"{len(blocks)} blocks, {empty_blocks} empty"))

    # List coverage
    list_types = set(l['list_type'] for l in lists)
    checks.append(("List types identified", len(list_types) >= 5, f"{len(list_types)} types"))

    # DDx extraction
    ddx_count = ddx['metadata']['total_differential_lists']
    checks.append(("Differential diagnoses", ddx_count >= 100, f"{ddx_count} lists"))

    # Table extraction
    checks.append(("Tables extracted", len(tables) == 21, f"{len(tables)}/21"))

    # Critical chapters
    ch3_blocks = sum(1 for b in blocks if b['chapter_number'] == 3)
    checks.append(("Chapter 3 (Trauma) blocks", ch3_blocks > 100, f"{ch3_blocks} blocks"))

    # Print results
    print("\nValidation Results:")
    for check, passed, detail in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check}: {detail}")

    passed_count = sum(1 for _, p, _ in checks if p)
    print(f"\n{passed_count}/{len(checks)} checks passed")

    # Summary stats
    print("\nSummary Statistics:")
    print(f"  Chapters: {len(chapters)}")
    print(f"  Text blocks: {len(blocks)}")
    print(f"  Lists: {len(lists)}")
    print(f"  Tables: {len(tables)}")
    print(f"  Differential diagnoses: {ddx_count}")

    # By chapter
    ch_stats = {}
    for b in blocks:
        ch = b['chapter_number']
        ch_stats[ch] = ch_stats.get(ch, 0) + 1

    print(f"\nBlocks by Chapter:")
    for ch in sorted(ch_stats.keys()):
        print(f"  Ch {ch:2d}: {ch_stats[ch]:4d} blocks")

    return passed_count == len(checks)

if __name__ == '__main__':
    success = validate_phase1()
    sys.exit(0 if success else 1)
