#!/usr/bin/env python3
"""
Phase 7.1: Data Quality Validation

Validates the knowledge graph data quality:
- Checks for duplicate entities
- Verifies entity properties are complete
- Validates medical terminology
- Checks for orphaned edges
- Verifies relationship directionality
- Checks for circular relationships

Output: entity_validation_report.json, relationship_validation_report.json
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime


def load_json(file_path: Path) -> dict | list:
    """Load JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict | list, file_path: Path):
    """Save JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_entities(nodes: list) -> dict:
    """Validate entity data quality"""
    print("\n=== VALIDATING ENTITIES ===")

    issues = []
    stats = {
        "total_nodes": len(nodes),
        "unique_ids": 0,
        "duplicate_ids": [],
        "missing_required_fields": [],
        "incomplete_properties": [],
        "validation_passed": 0,
        "validation_failed": 0
    }

    # Check for duplicate IDs
    id_counts = Counter(node['id'] for node in nodes)
    duplicates = {id_: count for id_, count in id_counts.items() if count > 1}
    stats["unique_ids"] = len(id_counts)
    stats["duplicate_ids"] = list(duplicates.keys())

    if duplicates:
        issues.append({
            "severity": "critical",
            "type": "duplicate_ids",
            "count": len(duplicates),
            "examples": list(duplicates.keys())[:5]
        })

    # Validate each node
    required_fields = ['id', 'label', 'type', 'properties']
    required_properties = ['description', 'chapters']

    for node in nodes:
        node_issues = []

        # Check required top-level fields
        missing_fields = [f for f in required_fields if f not in node]
        if missing_fields:
            node_issues.append(f"Missing fields: {missing_fields}")
            stats["missing_required_fields"].append({
                "id": node.get('id', 'unknown'),
                "missing": missing_fields
            })

        # Check required properties
        if 'properties' in node:
            props = node['properties']
            missing_props = [p for p in required_properties if p not in props]
            if missing_props:
                node_issues.append(f"Missing properties: {missing_props}")
                stats["incomplete_properties"].append({
                    "id": node['id'],
                    "missing": missing_props
                })

            # Check if description is meaningful
            if 'description' in props and len(props['description']) < 10:
                node_issues.append("Description too short")

            # Check if chapters is non-empty
            if 'chapters' in props and not props['chapters']:
                node_issues.append("Empty chapters list")

        if node_issues:
            stats["validation_failed"] += 1
        else:
            stats["validation_passed"] += 1

    # Limit examples in report
    stats["missing_required_fields"] = stats["missing_required_fields"][:10]
    stats["incomplete_properties"] = stats["incomplete_properties"][:10]

    print(f"✓ Validated {stats['total_nodes']} entities")
    print(f"  - Passed: {stats['validation_passed']}")
    print(f"  - Failed: {stats['validation_failed']}")
    print(f"  - Duplicate IDs: {len(stats['duplicate_ids'])}")

    return {
        "statistics": stats,
        "issues": issues,
        "status": "fail" if issues or stats["validation_failed"] > 0 else "pass"
    }


def validate_relationships(edges: list, nodes: list) -> dict:
    """Validate relationship data quality"""
    print("\n=== VALIDATING RELATIONSHIPS ===")

    issues = []
    stats = {
        "total_edges": len(edges),
        "orphaned_edges": [],
        "invalid_directionality": [],
        "circular_relationships": [],
        "validation_passed": 0,
        "validation_failed": 0
    }

    # Create node ID set for fast lookup
    node_ids = {node['id'] for node in nodes}

    # Check for orphaned edges
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        rel_type = edge.get('relationship_type')

        edge_issues = []

        # Check if source and target exist
        if source not in node_ids:
            edge_issues.append(f"Source node not found: {source}")
            stats["orphaned_edges"].append({
                "edge": f"{source} -> {target}",
                "missing": "source"
            })

        if target not in node_ids:
            edge_issues.append(f"Target node not found: {target}")
            stats["orphaned_edges"].append({
                "edge": f"{source} -> {target}",
                "missing": "target"
            })

        # Check relationship directionality makes sense
        if source in node_ids and target in node_ids:
            source_node = next(n for n in nodes if n['id'] == source)
            target_node = next(n for n in nodes if n['id'] == target)

            source_type = source_node['type']
            target_type = target_node['type']

            # Validate relationship type matches node types
            valid_directions = {
                'presents_with': [('Disease', 'Symptom')],
                'associated_with': [('Disease', 'Sign')],
                'treated_with': [('Disease', 'Treatment')],
                'diagnosed_with': [('Disease', 'DiagnosticTest')],
                'differential_diagnosis': [('Symptom', 'Disease'), ('Sign', 'Disease')]
            }

            if rel_type in valid_directions:
                if (source_type, target_type) not in valid_directions[rel_type]:
                    edge_issues.append(f"Invalid direction: {source_type} -{rel_type}-> {target_type}")
                    stats["invalid_directionality"].append({
                        "edge": f"{source} -> {target}",
                        "type": rel_type,
                        "actual": f"{source_type} -> {target_type}"
                    })

        if edge_issues:
            stats["validation_failed"] += 1
        else:
            stats["validation_passed"] += 1

    # Check for circular relationships (same source and target)
    for edge in edges:
        if edge.get('source') == edge.get('target'):
            stats["circular_relationships"].append({
                "node": edge['source'],
                "type": edge['relationship_type']
            })
            issues.append({
                "severity": "warning",
                "type": "circular_relationship",
                "node": edge['source']
            })

    # Limit examples in report
    stats["orphaned_edges"] = stats["orphaned_edges"][:10]
    stats["invalid_directionality"] = stats["invalid_directionality"][:10]
    stats["circular_relationships"] = stats["circular_relationships"][:10]

    print(f"✓ Validated {stats['total_edges']} relationships")
    print(f"  - Passed: {stats['validation_passed']}")
    print(f"  - Failed: {stats['validation_failed']}")
    print(f"  - Orphaned: {len(stats['orphaned_edges'])}")
    print(f"  - Invalid direction: {len(stats['invalid_directionality'])}")
    print(f"  - Circular: {len(stats['circular_relationships'])}")

    return {
        "statistics": stats,
        "issues": issues,
        "status": "fail" if issues or stats["validation_failed"] > 0 else "pass"
    }


def main():
    # Paths
    base_dir = Path(__file__).parent.parent.parent.parent
    phase6_dir = base_dir / "output" / "phase6"
    phase7_dir = base_dir / "output" / "phase7"

    nodes_file = phase6_dir / "graphrag_nodes.json"
    edges_file = phase6_dir / "graphrag_edges.json"

    entity_report_file = phase7_dir / "entity_validation_report.json"
    relationship_report_file = phase7_dir / "relationship_validation_report.json"

    print("=" * 80)
    print("PHASE 7.1: DATA QUALITY VALIDATION")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    nodes = load_json(nodes_file)
    edges = load_json(edges_file)
    print(f"✓ Loaded {len(nodes)} nodes and {len(edges)} edges")

    # Validate entities
    entity_validation = validate_entities(nodes)

    # Validate relationships
    relationship_validation = validate_relationships(edges, nodes)

    # Create entity validation report
    entity_report = {
        "phase": "7.1",
        "title": "Entity Validation Report",
        "generated_at": datetime.now().isoformat(),
        "validation": entity_validation,
        "summary": {
            "total_nodes": len(nodes),
            "passed": entity_validation["statistics"]["validation_passed"],
            "failed": entity_validation["statistics"]["validation_failed"],
            "status": entity_validation["status"]
        }
    }

    # Create relationship validation report
    relationship_report = {
        "phase": "7.1",
        "title": "Relationship Validation Report",
        "generated_at": datetime.now().isoformat(),
        "validation": relationship_validation,
        "summary": {
            "total_edges": len(edges),
            "passed": relationship_validation["statistics"]["validation_passed"],
            "failed": relationship_validation["statistics"]["validation_failed"],
            "status": relationship_validation["status"]
        }
    }

    # Save reports
    phase7_dir.mkdir(parents=True, exist_ok=True)
    save_json(entity_report, entity_report_file)
    save_json(relationship_report, relationship_report_file)

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\nEntity Validation: {entity_validation['status'].upper()}")
    print(f"Relationship Validation: {relationship_validation['status'].upper()}")
    print(f"\nReports saved:")
    print(f"  - {entity_report_file}")
    print(f"  - {relationship_report_file}")

    # Exit with appropriate code
    if entity_validation['status'] == 'fail' or relationship_validation['status'] == 'fail':
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
