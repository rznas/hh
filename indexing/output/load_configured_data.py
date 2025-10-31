#!/usr/bin/env python3
"""
Helper module for loading extraction data based on configuration.

This module provides utilities for downstream phases (Phase 4+) to load
entities and edges according to the active extraction configuration.

Usage:
    from load_configured_data import ConfiguredDataLoader

    # Initialize loader
    loader = ConfiguredDataLoader()

    # Load specific entity type
    diseases = loader.load_entities("diseases")
    anatomy = loader.load_entities("anatomy")

    # Load all entities
    all_entities = loader.load_all_entities()

    # Load specific edge type
    caused_by_edges = loader.load_edges("caused_by")

    # Load all edges
    all_edges = loader.load_all_edges()

    # Get statistics
    stats = loader.get_stats()
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ConfiguredDataLoader:
    """Load extraction data based on active configuration."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize loader with configuration file.

        Args:
            config_file: Path to extraction_config.json (defaults to same directory)
        """
        if config_file is None:
            config_file = Path(__file__).parent / "extraction_config.json"

        self.config_file = config_file
        self.output_dir = Path(__file__).parent
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration file."""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_file_path(self, relative_path: str) -> Path:
        """Resolve relative path to absolute path."""
        return self.output_dir / relative_path

    def _get_active_file(self, source_config: Dict) -> Optional[Path]:
        """Get active file path from source configuration."""
        active_mode = source_config.get("active_mode", "baseline")
        active_file = source_config.get(active_mode)

        if not active_file:
            return None

        return self._resolve_file_path(active_file)

    def load_entities(self, entity_type: str) -> List[Dict]:
        """
        Load entities of a specific type.

        Args:
            entity_type: Entity type name (e.g., "diseases", "anatomy", "etiology")

        Returns:
            List of entity dictionaries

        Raises:
            ValueError: If entity type not found in config
            FileNotFoundError: If configured file doesn't exist
        """
        entity_sources = self.config.get("entity_sources", {})

        if entity_type not in entity_sources:
            raise ValueError(f"Unknown entity type: {entity_type}")

        file_path = self._get_active_file(entity_sources[entity_type])

        if not file_path:
            raise ValueError(f"No active file configured for entity type: {entity_type}")

        if not file_path.exists():
            raise FileNotFoundError(f"Entity file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Add source metadata
        active_mode = entity_sources[entity_type].get("active_mode", "baseline")
        for entity in data:
            if "metadata" not in entity:
                entity["metadata"] = {}
            entity["metadata"]["loaded_from"] = str(file_path)
            entity["metadata"]["config_mode"] = active_mode

        return data

    def load_all_entities(self) -> Dict[str, List[Dict]]:
        """
        Load all configured entity types.

        Returns:
            Dictionary mapping entity type name to list of entities
        """
        all_entities = {}

        for entity_type in self.config.get("entity_sources", {}).keys():
            try:
                all_entities[entity_type] = self.load_entities(entity_type)
            except (ValueError, FileNotFoundError) as e:
                print(f"⚠ Warning: Could not load {entity_type}: {e}")

        return all_entities

    def load_edges(self, edge_type: str) -> List[Dict]:
        """
        Load edges of a specific type.

        Args:
            edge_type: Edge type name (e.g., "caused_by", "affects")

        Returns:
            List of edge dictionaries

        Raises:
            ValueError: If edge type not found in config
            FileNotFoundError: If configured file doesn't exist
        """
        edge_sources = self.config.get("edge_sources", {})

        if edge_type not in edge_sources:
            raise ValueError(f"Unknown edge type: {edge_type}")

        file_path = self._get_active_file(edge_sources[edge_type])

        if not file_path:
            raise ValueError(f"No active file configured for edge type: {edge_type}")

        if not file_path.exists():
            raise FileNotFoundError(f"Edge file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle legacy format (filter by relationship_type if needed)
        note = edge_sources[edge_type].get("note", "")
        if "filter by relationship_type" in note:
            # Filter edges by relationship_type
            data = [edge for edge in data if edge.get("relationship_type") == edge_type]

        # Add source metadata
        active_mode = edge_sources[edge_type].get("active_mode", "baseline")
        for edge in data:
            if "metadata" not in edge:
                edge["metadata"] = {}
            edge["metadata"]["loaded_from"] = str(file_path)
            edge["metadata"]["config_mode"] = active_mode

        return data

    def load_all_edges(self) -> Dict[str, List[Dict]]:
        """
        Load all configured edge types.

        Returns:
            Dictionary mapping edge type name to list of edges
        """
        all_edges = {}

        for edge_type in self.config.get("edge_sources", {}).keys():
            try:
                all_edges[edge_type] = self.load_edges(edge_type)
            except (ValueError, FileNotFoundError) as e:
                print(f"⚠ Warning: Could not load {edge_type}: {e}")

        return all_edges

    def get_stats(self) -> Dict:
        """
        Get statistics about loaded data.

        Returns:
            Dictionary with entity and edge counts
        """
        stats = {
            "entities": {},
            "edges": {},
            "total_entities": 0,
            "total_edges": 0,
            "active_modes": {"entities": {}, "edges": {}}
        }

        # Entity stats
        for entity_type, entity_config in self.config.get("entity_sources", {}).items():
            try:
                entities = self.load_entities(entity_type)
                count = len(entities)
                stats["entities"][entity_type] = count
                stats["total_entities"] += count
                stats["active_modes"]["entities"][entity_type] = entity_config.get("active_mode", "baseline")
            except (ValueError, FileNotFoundError):
                stats["entities"][entity_type] = 0

        # Edge stats
        for edge_type, edge_config in self.config.get("edge_sources", {}).items():
            try:
                edges = self.load_edges(edge_type)
                count = len(edges)
                stats["edges"][edge_type] = count
                stats["total_edges"] += count
                stats["active_modes"]["edges"][edge_type] = edge_config.get("active_mode", "baseline")
            except (ValueError, FileNotFoundError):
                stats["edges"][edge_type] = 0

        return stats

    def print_stats(self):
        """Print statistics in a formatted way."""
        stats = self.get_stats()

        print("=" * 80)
        print("CONFIGURED DATA STATISTICS")
        print("=" * 80)

        print("\n📦 ENTITIES:")
        for entity_type, count in sorted(stats["entities"].items()):
            mode = stats["active_modes"]["entities"].get(entity_type, "?")
            print(f"  {entity_type:20s} [{mode:8s}] {count:6,d} entities")

        print(f"\n  Total Entities: {stats['total_entities']:,}")

        print("\n🔗 EDGES:")
        for edge_type, count in sorted(stats["edges"].items()):
            mode = stats["active_modes"]["edges"].get(edge_type, "?")
            print(f"  {edge_type:20s} [{mode:8s}] {count:6,d} edges")

        print(f"\n  Total Edges: {stats['total_edges']:,}")
        print("=" * 80)


def main():
    """Example usage and testing."""
    print("Testing ConfiguredDataLoader...\n")

    loader = ConfiguredDataLoader()

    # Print statistics
    loader.print_stats()

    # Example: Load specific entities
    print("\n" + "=" * 80)
    print("EXAMPLE: Loading specific entity types")
    print("=" * 80)

    try:
        diseases = loader.load_entities("diseases")
        print(f"✓ Loaded {len(diseases)} diseases")

        anatomy = loader.load_entities("anatomy")
        print(f"✓ Loaded {len(anatomy)} anatomy entities")

    except Exception as e:
        print(f"⚠ Error: {e}")

    # Example: Load specific edges
    print("\n" + "=" * 80)
    print("EXAMPLE: Loading specific edge types")
    print("=" * 80)

    try:
        caused_by = loader.load_edges("caused_by")
        print(f"✓ Loaded {len(caused_by)} caused_by edges")

        affects = loader.load_edges("affects")
        print(f"✓ Loaded {len(affects)} affects edges")

    except Exception as e:
        print(f"⚠ Error: {e}")


if __name__ == "__main__":
    main()
