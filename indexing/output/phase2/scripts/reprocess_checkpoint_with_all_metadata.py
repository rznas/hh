#!/usr/bin/env python3
"""
Reprocess Phase 2 checkpoint to preserve all chapter/section metadata.

This script loads the phase2_checkpoint.json file, applies the updated deduplication
logic that preserves ALL chapter and section references where each entity was mentioned,
and regenerates all entity JSON files.

Usage:
    python reprocess_checkpoint_with_all_metadata.py
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


# Paths
PHASE2_DIR = Path(__file__).parent.parent
CHECKPOINT_FILE = PHASE2_DIR / "phase2_checkpoint.json"


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for deduplication."""
    return name.lower().strip()


def deduplicate_entities(all_entities: List[Dict]) -> Dict[str, Dict]:
    """
    Deduplicate entities, keeping highest confidence version.
    Preserves all chapter/section references where entity was mentioned.
    Returns dict with normalized name as key.
    """
    entity_map = {}

    for entity in all_entities:
        # Normalize name for comparison
        normalized = normalize_entity_name(entity["name"])

        if normalized not in entity_map:
            # First occurrence - convert metadata to list
            entity_copy = entity.copy()
            if "metadata" in entity_copy:
                entity_copy["metadata"] = [entity_copy["metadata"]]
            entity_map[normalized] = entity_copy
        else:
            # Entity already exists - merge information
            existing = entity_map[normalized]

            # Keep entity with higher confidence for main attributes
            if entity.get("confidence", 0.7) > existing.get("confidence", 0.7):
                # Update main attributes from higher confidence entity
                existing["name"] = entity["name"]
                existing["confidence"] = entity["confidence"]
                if "description" in entity:
                    existing["description"] = entity["description"]

            # Always merge synonyms
            existing_synonyms = set(existing.get("synonyms", []))
            new_synonyms = set(entity.get("synonyms", []))
            merged_synonyms = existing_synonyms | new_synonyms
            if merged_synonyms:
                existing["synonyms"] = sorted(list(merged_synonyms))

            # Always append metadata (chapter/section references)
            if "metadata" in entity:
                if "metadata" not in existing:
                    existing["metadata"] = []
                elif not isinstance(existing["metadata"], list):
                    existing["metadata"] = [existing["metadata"]]

                # Add new metadata if not duplicate
                new_meta = entity["metadata"]
                # Check if this exact chapter/section combo already exists
                is_duplicate = False
                for existing_meta in existing["metadata"]:
                    if (existing_meta.get("chapter") == new_meta.get("chapter") and
                        existing_meta.get("section") == new_meta.get("section") and
                        existing_meta.get("block_index") == new_meta.get("block_index")):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    existing["metadata"].append(new_meta)

    return entity_map


def create_entity_id(entity_type: str, index: int) -> str:
    """Generate entity ID based on type."""
    type_map = {
        'disease': 'disease',
        'symptom': 'symptom',
        'sign': 'sign',
        'treatment': 'treatment',
        'medication': 'medication',
        'procedure': 'procedure',
        'anatomy': 'anatomy',
        'etiology': 'etiology',
        'risk_factor': 'risk_factor',
        'differential': 'differential',
        'complication': 'complication',
        'lab_test': 'lab_test',
        'imaging': 'imaging'
    }
    prefix = type_map.get(entity_type.lower(), 'entity')
    return f"{prefix}_{index:03d}"


def save_entities_by_type(all_entities_dict: Dict[str, Dict], output_dir: Path) -> Dict[str, int]:
    """
    Organize entities by type and save to separate files.
    Returns dict with count of entities saved by type.
    """
    entities_by_type = defaultdict(list)

    # Organize by type
    for normalized_name, entity in all_entities_dict.items():
        entity_type = entity.get("type", "").lower()
        entities_by_type[entity_type].append(entity)

    # Save each type with entity IDs
    saved_counts = {}
    for entity_type, entities in entities_by_type.items():
        # Add entity_id to each entity
        for idx, entity in enumerate(entities, 1):
            entity["entity_id"] = create_entity_id(entity_type, idx)
            # Ensure name is title case for display
            if "name" in entity:
                entity["name_normalized"] = normalize_entity_name(entity["name"])

        # Sort by name
        entities_sorted = sorted(entities, key=lambda e: e.get("name", "").lower())

        # Determine output filename
        if entity_type == 'lab_test':
            filename = output_dir / "lab_tests.json"
        else:
            filename = output_dir / f"{entity_type}s.json"

        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(entities_sorted, f, indent=2, ensure_ascii=False)

        saved_counts[entity_type] = len(entities_sorted)
        print(f"  ✓ Saved {len(entities_sorted)} {entity_type} entities to {filename.name}")

    return saved_counts


def main():
    """Main execution function."""
    print("=" * 80)
    print("Reprocess Phase 2 Checkpoint - Preserve All Metadata")
    print("=" * 80)

    # Check if checkpoint exists
    if not CHECKPOINT_FILE.exists():
        print(f"\n❌ ERROR: Checkpoint file not found: {CHECKPOINT_FILE}")
        print("Please ensure phase2_checkpoint.json exists in the output/phase2 directory.")
        return

    print(f"\n[1/3] Loading checkpoint from: {CHECKPOINT_FILE}")
    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)

    all_entities = checkpoint.get("entities", [])
    print(f"  ✓ Loaded {len(all_entities)} entities from checkpoint")

    # Show stats before deduplication
    stats = checkpoint.get("stats", {})
    print(f"\n  Extraction stats:")
    print(f"    • Blocks processed: {stats.get('blocks_processed', 0)}")
    print(f"    • Entities extracted: {stats.get('entities_extracted', 0)}")
    print(f"    • Total cost: ${stats.get('total_cost', 0):.2f}")

    # Count entities by type before deduplication
    by_type_before = defaultdict(int)
    for entity in all_entities:
        entity_type = entity.get("type", "").lower()
        by_type_before[entity_type] += 1

    print(f"\n  Entities by type (before deduplication):")
    for entity_type, count in sorted(by_type_before.items()):
        print(f"    • {entity_type}: {count}")

    # Deduplicate entities with new logic
    print(f"\n[2/3] Deduplicating entities (preserving all chapter/section references)...")
    unique_entities_dict = deduplicate_entities(all_entities)
    print(f"  ✓ Removed {len(all_entities) - len(unique_entities_dict)} duplicates")
    print(f"  ✓ Final count: {len(unique_entities_dict)} unique entities")

    # Show sample entity with multiple metadata entries
    sample_with_multiple = None
    max_metadata_count = 0
    for entity in unique_entities_dict.values():
        metadata = entity.get("metadata", [])
        if isinstance(metadata, list) and len(metadata) > max_metadata_count:
            max_metadata_count = len(metadata)
            sample_with_multiple = entity

    if sample_with_multiple and max_metadata_count > 1:
        print(f"\n  Example: Entity '{sample_with_multiple.get('name')}' appears in {max_metadata_count} locations")
        print(f"    Chapters/sections:")
        for meta in sample_with_multiple["metadata"][:5]:  # Show first 5
            print(f"      • Chapter {meta.get('chapter')}: {meta.get('section')}")
        if max_metadata_count > 5:
            print(f"      ... and {max_metadata_count - 5} more locations")

    # Save entities by type
    print(f"\n[3/3] Saving entities by type to {PHASE2_DIR}...")
    saved_counts = save_entities_by_type(unique_entities_dict, PHASE2_DIR/"out/")

    # Print summary
    print("\n" + "=" * 80)
    print("REPROCESSING COMPLETE")
    print("=" * 80)
    print(f"Total Unique Entities: {len(unique_entities_dict)}")
    print(f"\nEntities by type (after deduplication):")
    for entity_type, count in sorted(saved_counts.items()):
        before_count = by_type_before.get(entity_type, 0)
        duplicates = before_count - count
        print(f"  • {entity_type}: {count} (removed {duplicates} duplicates)")

    print(f"\n✓ All entity JSON files have been updated with preserved metadata!")
    print("=" * 80)


if __name__ == "__main__":
    main()
