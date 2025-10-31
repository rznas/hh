#!/usr/bin/env python3
"""
Phase 2 Compensation: Extract CHAPTER and SECTION entities (Issue 1.8)

This script extracts chapter and section structural entities from The Wills Eye Manual
to enable hierarchical knowledge graph organization.

Approach:
- Load Phase 1 structured chapters data
- Create CHAPTER entities for each chapter
- Create SECTION entities for each section
- Generate hierarchical IDs for proper belongs_to relationships

Input:
- Phase 1: wills_eye_chapters_structured.json

Output:
- chapters.json (chapter entities)
- sections.json (section entities)
- phase2_structure_report.json (extraction statistics)

Usage:
    .venv/bin/python indexing/output/phase2/scripts/phase2_extract_structure.py
    .venv/bin/python indexing/output/phase2/scripts/phase2_extract_structure.py --dry-run
"""

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

# Paths
SCRIPT_DIR = Path(__file__).parent
PHASE1_DIR = SCRIPT_DIR.parent.parent / "phase1"
PHASE2_DIR = SCRIPT_DIR.parent
INPUT_FILE = PHASE1_DIR / "wills_eye_chapters_structured.json"
CHAPTERS_FILE = PHASE2_DIR / "chapters.json"
SECTIONS_FILE = PHASE2_DIR / "sections.json"
REPORT_FILE = PHASE2_DIR / "phase2_structure_report.json"


@dataclass
class ChapterEntity:
    """Represents a chapter entity."""
    entity_id: str
    name: str
    chapter_number: int
    type: str = "chapter"
    section_count: int = 0
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "chapter_number": self.chapter_number,
            "type": self.type,
            "section_count": self.section_count,
            "metadata": self.metadata or {
                "extraction_method": "structural",
                "source": "wills_eye_manual_toc"
            }
        }


@dataclass
class SectionEntity:
    """Represents a section entity."""
    entity_id: str
    name: str
    chapter_number: int
    parent_chapter_id: str
    type: str = "section"
    level: int = 1  # Section hierarchy level (1, 2, 3, etc.)
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "chapter_number": self.chapter_number,
            "parent_chapter_id": self.parent_chapter_id,
            "type": self.type,
            "level": self.level,
            "metadata": self.metadata or {
                "extraction_method": "structural",
                "source": "wills_eye_manual_toc"
            }
        }


def load_structured_chapters() -> Dict:
    """Load Phase 1 structured chapters."""
    if not INPUT_FILE.exists():
        print(f"❌ Error: {INPUT_FILE} not found")
        return {}

    with open(INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def create_chapter_id(chapter_num: int) -> str:
    """Generate chapter entity ID."""
    return f"chapter_{chapter_num:02d}"


def create_section_id(chapter_num: int, section_idx: int) -> str:
    """Generate section entity ID."""
    return f"section_{chapter_num:02d}_{section_idx:03d}"


def extract_sections_recursive(sections_data: List, chapter_num: int, parent_id: str,
                                section_idx_counter: List[int], level: int = 1) -> List[SectionEntity]:
    """
    Recursively extract sections and subsections.
    section_idx_counter is a list with one element to maintain state across recursion.
    """
    section_entities = []

    if isinstance(sections_data, dict):
        sections_data = [sections_data]

    for section_data in sections_data:
        if isinstance(section_data, str):
            # Simple section string
            section_idx_counter[0] += 1
            section_id = create_section_id(chapter_num, section_idx_counter[0])

            entity = SectionEntity(
                entity_id=section_id,
                name=section_data,
                chapter_number=chapter_num,
                parent_chapter_id=parent_id,
                level=level
            )
            section_entities.append(entity)

        elif isinstance(section_data, dict):
            # Section with potential subsections
            section_name = section_data.get("section", section_data.get("title", "Unknown Section"))

            section_idx_counter[0] += 1
            section_id = create_section_id(chapter_num, section_idx_counter[0])

            entity = SectionEntity(
                entity_id=section_id,
                name=section_name,
                chapter_number=chapter_num,
                parent_chapter_id=parent_id,
                level=level
            )
            section_entities.append(entity)

            # Check for subsections
            if "subsections" in section_data:
                subsections = extract_sections_recursive(
                    section_data["subsections"],
                    chapter_num,
                    section_id,  # Parent is this section
                    section_idx_counter,
                    level + 1
                )
                section_entities.extend(subsections)

    return section_entities


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract CHAPTER and SECTION entities")
    parser.add_argument("--dry-run", action="store_true", help="Preview without saving")
    args = parser.parse_args()

    print("=" * 80)
    print("Phase 2 Compensation: CHAPTER & SECTION Entity Extraction")
    print("=" * 80)
    print(f"Method: Structural extraction from TOC")
    print(f"Input: {INPUT_FILE}")
    print("=" * 80)

    # Load structured chapters
    print("\n[1/3] Loading structured chapters...")
    structured_data = load_structured_chapters()

    if not structured_data:
        print("❌ No structured chapters found. Exiting.")
        return

    chapters_data = structured_data.get("chapters", [])
    print(f"  ✓ Loaded {len(chapters_data)} chapters")

    # Extract chapters and sections
    print("\n[2/3] Extracting chapters and sections...")
    chapter_entities = []
    all_section_entities = []

    for chapter_data in chapters_data:
        chapter_num = chapter_data.get("chapter_number", 0)
        chapter_title = chapter_data.get("chapter_title", f"Chapter {chapter_num}")

        # Create chapter entity
        chapter_id = create_chapter_id(chapter_num)
        chapter_entity = ChapterEntity(
            entity_id=chapter_id,
            name=chapter_title,
            chapter_number=chapter_num
        )

        # Extract sections
        sections_data = chapter_data.get("sections", [])
        section_idx_counter = [0]  # Mutable counter for recursion

        section_entities = extract_sections_recursive(
            sections_data,
            chapter_num,
            chapter_id,
            section_idx_counter,
            level=1
        )

        # Update chapter section count
        chapter_entity.section_count = len(section_entities)

        chapter_entities.append(chapter_entity)
        all_section_entities.extend(section_entities)

    print(f"  ✓ Extracted {len(chapter_entities)} chapters")
    print(f"  ✓ Extracted {len(all_section_entities)} sections")

    # Show samples
    print("\n  Sample chapters:")
    for ch in chapter_entities[:5]:
        print(f"    • [{ch.entity_id}] {ch.name} ({ch.section_count} sections)")

    print("\n  Sample sections:")
    for sec in all_section_entities[:5]:
        print(f"    • [{sec.entity_id}] {sec.name} (Level {sec.level})")

    if args.dry_run:
        print("\n[DRY RUN] Would save:")
        print(f"  • {CHAPTERS_FILE} ({len(chapter_entities)} entities)")
        print(f"  • {SECTIONS_FILE} ({len(all_section_entities)} entities)")
        return

    # Save files
    print("\n[3/3] Saving entities...")

    chapters_json = [ch.to_dict() for ch in chapter_entities]
    with open(CHAPTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(chapters_json, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(chapter_entities)} chapters to {CHAPTERS_FILE}")

    sections_json = [sec.to_dict() for sec in all_section_entities]
    with open(SECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sections_json, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved {len(all_section_entities)} sections to {SECTIONS_FILE}")

    # Generate report
    chapter_section_map = {}
    section_levels = {1: 0, 2: 0, 3: 0, 4: 0}

    for ch in chapter_entities:
        chapter_section_map[ch.chapter_number] = ch.section_count

    for sec in all_section_entities:
        if sec.level in section_levels:
            section_levels[sec.level] += 1

    report = {
        "extraction_method": "structural",
        "total_chapters": len(chapter_entities),
        "total_sections": len(all_section_entities),
        "avg_sections_per_chapter": round(len(all_section_entities) / len(chapter_entities), 1) if chapter_entities else 0,
        "section_levels": section_levels,
        "chapter_section_distribution": chapter_section_map,
        "chapters": [
            {
                "id": ch.entity_id,
                "name": ch.name,
                "number": ch.chapter_number,
                "sections": ch.section_count
            }
            for ch in chapter_entities
        ]
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"  ✓ Saved report to {REPORT_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print(f"Total Chapters: {len(chapter_entities)}")
    print(f"Total Sections: {len(all_section_entities)}")
    print(f"Avg Sections/Chapter: {report['avg_sections_per_chapter']}")
    print(f"\nSection Levels:")
    for level, count in sorted(section_levels.items()):
        if count > 0:
            print(f"  • Level {level}: {count}")
    print("=" * 80)


if __name__ == "__main__":
    main()
