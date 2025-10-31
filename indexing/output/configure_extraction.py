#!/usr/bin/env python3
"""
Extraction Configuration Manager

This utility manages switching between baseline and LLM extraction outputs.

Usage:
    # Show current configuration
    python configure_extraction.py --show

    # Set all entities to LLM mode
    python configure_extraction.py --set-mode llm

    # Set specific entity to LLM mode
    python configure_extraction.py --set anatomy=llm etiology=baseline

    # Set all edges to LLM mode
    python configure_extraction.py --set-edges llm

    # Get resolved file paths for downstream phases
    python configure_extraction.py --resolve

    # Validate that configured files exist
    python configure_extraction.py --validate
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_FILE = Path(__file__).parent / "extraction_config.json"
OUTPUT_DIR = Path(__file__).parent


def load_config() -> Dict:
    """Load extraction configuration."""
    if not CONFIG_FILE.exists():
        print(f"❌ Config file not found: {CONFIG_FILE}")
        return {}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: Dict):
    """Save extraction configuration."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print(f"✓ Configuration saved to {CONFIG_FILE}")


def show_config(config: Dict):
    """Display current configuration."""
    print("=" * 80)
    print("EXTRACTION CONFIGURATION")
    print("=" * 80)
    print(f"Default Mode: {config.get('default_mode', 'baseline')}")

    print("\n📦 ENTITY SOURCES:")
    print("-" * 80)
    for entity_name, entity_config in config.get("entity_sources", {}).items():
        active_mode = entity_config.get("active_mode", "baseline")
        active_file = entity_config.get(active_mode, "N/A")

        # Check if file exists
        file_path = OUTPUT_DIR / active_file if active_file != "N/A" else None
        exists = "✓" if file_path and file_path.exists() else "✗"

        print(f"  {entity_name:20s} [{active_mode:8s}] {exists} {active_file}")

        if entity_config.get("note"):
            print(f"    ℹ {entity_config['note']}")

    print("\n🔗 EDGE SOURCES:")
    print("-" * 80)
    for edge_name, edge_config in config.get("edge_sources", {}).items():
        active_mode = edge_config.get("active_mode", "baseline")
        active_file = edge_config.get(active_mode, "N/A")

        # Check if file exists
        file_path = OUTPUT_DIR / active_file if active_file != "N/A" else None
        exists = "✓" if file_path and file_path.exists() else "✗"

        print(f"  {edge_name:20s} [{active_mode:8s}] {exists} {active_file}")

        if edge_config.get("note"):
            print(f"    ℹ {edge_config['note']}")

    print("=" * 80)


def set_mode(config: Dict, mode: str, entity_type: str = "all"):
    """Set extraction mode for entities/edges."""
    valid_modes = ["baseline", "llm"]

    if mode not in valid_modes:
        print(f"❌ Invalid mode: {mode}. Must be one of {valid_modes}")
        return False

    if entity_type == "all":
        # Set all entities
        for entity_name, entity_config in config.get("entity_sources", {}).items():
            if entity_config.get(mode):  # Only if LLM version exists
                entity_config["active_mode"] = mode

        # Set all edges
        for edge_name, edge_config in config.get("edge_sources", {}).items():
            if edge_config.get(mode):  # Only if LLM version exists
                edge_config["active_mode"] = mode

        print(f"✓ Set all sources to '{mode}' mode")

    else:
        # Set specific entity/edge
        if entity_type in config.get("entity_sources", {}):
            entity_config = config["entity_sources"][entity_type]
            if entity_config.get(mode):
                entity_config["active_mode"] = mode
                print(f"✓ Set {entity_type} to '{mode}' mode")
            else:
                print(f"⚠ No '{mode}' version available for {entity_type}")
                return False

        elif entity_type in config.get("edge_sources", {}):
            edge_config = config["edge_sources"][entity_type]
            if edge_config.get(mode):
                edge_config["active_mode"] = mode
                print(f"✓ Set {entity_type} to '{mode}' mode")
            else:
                print(f"⚠ No '{mode}' version available for {entity_type}")
                return False

        else:
            print(f"❌ Unknown entity/edge type: {entity_type}")
            return False

    return True


def set_edges_mode(config: Dict, mode: str):
    """Set mode for all edges."""
    valid_modes = ["baseline", "llm"]

    if mode not in valid_modes:
        print(f"❌ Invalid mode: {mode}")
        return False

    count = 0
    for edge_name, edge_config in config.get("edge_sources", {}).items():
        if edge_config.get(mode):
            edge_config["active_mode"] = mode
            count += 1

    print(f"✓ Set {count} edge sources to '{mode}' mode")
    return True


def resolve_paths(config: Dict):
    """Resolve active file paths for all entities and edges."""
    print("=" * 80)
    print("RESOLVED FILE PATHS")
    print("=" * 80)

    resolved = {
        "entities": {},
        "edges": {}
    }

    print("\n📦 ENTITIES:")
    for entity_name, entity_config in config.get("entity_sources", {}).items():
        active_mode = entity_config.get("active_mode", "baseline")
        active_file = entity_config.get(active_mode)

        if active_file:
            full_path = OUTPUT_DIR / active_file
            resolved["entities"][entity_name] = str(full_path)
            print(f"  {entity_name:20s} → {full_path}")

    print("\n🔗 EDGES:")
    for edge_name, edge_config in config.get("edge_sources", {}).items():
        active_mode = edge_config.get("active_mode", "baseline")
        active_file = edge_config.get(active_mode)

        if active_file:
            full_path = OUTPUT_DIR / active_file
            resolved["edges"][edge_name] = str(full_path)
            print(f"  {edge_name:20s} → {full_path}")

    # Save resolved paths
    resolved_file = OUTPUT_DIR / "resolved_paths.json"
    with open(resolved_file, "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=2)

    print(f"\n✓ Saved resolved paths to {resolved_file}")
    print("=" * 80)


def validate_config(config: Dict):
    """Validate that configured files exist."""
    print("=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)

    missing_entities = []
    missing_edges = []

    print("\n📦 ENTITIES:")
    for entity_name, entity_config in config.get("entity_sources", {}).items():
        active_mode = entity_config.get("active_mode", "baseline")
        active_file = entity_config.get(active_mode)

        if active_file:
            file_path = OUTPUT_DIR / active_file
            exists = file_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {entity_name:20s} [{active_mode:8s}] {active_file}")

            if not exists:
                missing_entities.append((entity_name, active_file))

    print("\n🔗 EDGES:")
    for edge_name, edge_config in config.get("edge_sources", {}).items():
        active_mode = edge_config.get("active_mode", "baseline")
        active_file = edge_config.get(active_mode)

        if active_file:
            file_path = OUTPUT_DIR / active_file
            exists = file_path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {edge_name:20s} [{active_mode:8s}] {active_file}")

            if not exists:
                missing_edges.append((edge_name, active_file))

    # Summary
    print("\n" + "=" * 80)
    if missing_entities or missing_edges:
        print("⚠ VALIDATION FAILED")
        print(f"  Missing entities: {len(missing_entities)}")
        print(f"  Missing edges: {len(missing_edges)}")

        if missing_entities:
            print("\n  Missing entity files:")
            for entity_name, file_path in missing_entities:
                print(f"    • {entity_name}: {file_path}")

        if missing_edges:
            print("\n  Missing edge files:")
            for edge_name, file_path in missing_edges:
                print(f"    • {edge_name}: {file_path}")

        print("\n  💡 Run compensation scripts to generate missing files.")
    else:
        print("✓ VALIDATION PASSED - All configured files exist")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Manage extraction configuration for baseline vs LLM outputs"
    )

    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--set-mode", type=str, metavar="MODE", help="Set mode for all sources (baseline|llm)")
    parser.add_argument("--set-edges", type=str, metavar="MODE", help="Set mode for all edges (baseline|llm)")
    parser.add_argument("--set", nargs="+", metavar="ENTITY=MODE", help="Set specific entity/edge mode (e.g., anatomy=llm)")
    parser.add_argument("--resolve", action="store_true", help="Resolve and save active file paths")
    parser.add_argument("--validate", action="store_true", help="Validate that configured files exist")

    args = parser.parse_args()

    # Load config
    config = load_config()
    if not config:
        return

    # Execute command
    if args.show:
        show_config(config)

    elif args.set_mode:
        if set_mode(config, args.set_mode, "all"):
            save_config(config)
            show_config(config)

    elif args.set_edges:
        if set_edges_mode(config, args.set_edges):
            save_config(config)
            show_config(config)

    elif args.set:
        changes_made = False
        for setting in args.set:
            if "=" not in setting:
                print(f"❌ Invalid format: {setting}. Use ENTITY=MODE")
                continue

            entity_type, mode = setting.split("=", 1)
            if set_mode(config, mode, entity_type):
                changes_made = True

        if changes_made:
            save_config(config)
            show_config(config)

    elif args.resolve:
        resolve_paths(config)

    elif args.validate:
        validate_config(config)

    else:
        # Default: show config
        show_config(config)


if __name__ == "__main__":
    main()
