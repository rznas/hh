#!/usr/bin/env python3
"""
Phase 7.2: Medical Accuracy Validation

Validates medical accuracy of the knowledge graph:
- Validates red flags are correct
- Validates urgency classifications
- Cross-references with source data
- Checks for medical consistency

Output: red_flag_validation_report.json, urgency_validation_report.json
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


def load_json(file_path: Path) -> dict | list:
    """Load JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict | list, file_path: Path):
    """Save JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def validate_red_flags(nodes: list, red_flags_source: list) -> dict:
    """Validate red flag conditions"""
    print("\n=== VALIDATING RED FLAGS ===")

    issues = []
    stats = {
        "total_red_flags_in_graph": 0,
        "total_red_flags_in_source": len(red_flags_source),
        "red_flags_by_type": {},
        "missing_red_flags": [],
        "extra_red_flags": [],
        "coverage": 0.0
    }

    # Get all red flag nodes
    red_flag_nodes = [n for n in nodes if n['properties'].get('red_flag', False)]
    stats["total_red_flags_in_graph"] = len(red_flag_nodes)

    # Count by type
    type_counts = Counter(n['type'] for n in red_flag_nodes)
    stats["red_flags_by_type"] = dict(type_counts)

    # Create mapping of red flag conditions from source
    source_conditions = {rf['condition'].lower() for rf in red_flags_source}
    graph_conditions = {n['label'].lower() for n in red_flag_nodes if n['type'] == 'Disease'}

    # Check coverage
    missing = source_conditions - graph_conditions
    extra = graph_conditions - source_conditions

    stats["missing_red_flags"] = list(missing)[:10]
    stats["extra_red_flags"] = list(extra)[:10]

    if source_conditions:
        stats["coverage"] = len(source_conditions & graph_conditions) / len(source_conditions) * 100

    # Validate each red flag has urgency = emergent
    for node in red_flag_nodes:
        if node['type'] == 'Disease':
            urgency = node['properties'].get('urgency_level')
            if urgency != 'emergent':
                issues.append({
                    "severity": "critical",
                    "type": "red_flag_urgency_mismatch",
                    "disease": node['label'],
                    "urgency": urgency,
                    "expected": "emergent"
                })

    # Validate red flags have source citations
    for node in red_flag_nodes:
        if node['type'] == 'Disease':
            if not node['properties'].get('urgency_source'):
                issues.append({
                    "severity": "warning",
                    "type": "missing_source_citation",
                    "disease": node['label']
                })

    print(f"✓ Red flags in graph: {stats['total_red_flags_in_graph']}")
    print(f"  - Coverage: {stats['coverage']:.1f}%")
    print(f"  - Missing from graph: {len(stats['missing_red_flags'])}")
    print(f"  - Extra in graph: {len(stats['extra_red_flags'])}")
    print(f"  - Critical issues: {len([i for i in issues if i['severity'] == 'critical'])}")

    return {
        "statistics": stats,
        "issues": issues[:20],  # Limit to first 20
        "status": "fail" if len([i for i in issues if i['severity'] == 'critical']) > 0 else "pass"
    }


def validate_urgency_classifications(nodes: list, urgency_criteria: dict) -> dict:
    """Validate urgency classifications"""
    print("\n=== VALIDATING URGENCY CLASSIFICATIONS ===")

    issues = []
    stats = {
        "total_diseases": 0,
        "diseases_with_urgency": 0,
        "diseases_without_urgency": 0,
        "urgency_distribution": {},
        "diseases_without_source": []
    }

    # Get all disease nodes
    disease_nodes = [n for n in nodes if n['type'] == 'Disease']
    stats["total_diseases"] = len(disease_nodes)

    # Count urgency levels
    urgency_counts = Counter()
    for node in disease_nodes:
        urgency = node['properties'].get('urgency_level')
        if urgency:
            stats["diseases_with_urgency"] += 1
            urgency_counts[urgency] += 1
        else:
            stats["diseases_without_urgency"] += 1

    stats["urgency_distribution"] = dict(urgency_counts)

    # Validate urgency values are valid
    valid_urgency_levels = {'emergent', 'urgent', 'non-urgent'}
    for node in disease_nodes:
        urgency = node['properties'].get('urgency_level')
        if urgency and urgency not in valid_urgency_levels:
            issues.append({
                "severity": "critical",
                "type": "invalid_urgency_level",
                "disease": node['label'],
                "urgency": urgency,
                "valid_values": list(valid_urgency_levels)
            })

    # Validate urgency has source citation
    for node in disease_nodes:
        urgency = node['properties'].get('urgency_level')
        source = node['properties'].get('urgency_source')
        if urgency and not source:
            stats["diseases_without_source"].append(node['label'])

    stats["diseases_without_source"] = stats["diseases_without_source"][:10]

    # Validate consistency with red flags
    for node in disease_nodes:
        is_red_flag = node['properties'].get('red_flag', False)
        urgency = node['properties'].get('urgency_level')
        if is_red_flag and urgency != 'emergent':
            issues.append({
                "severity": "critical",
                "type": "red_flag_urgency_inconsistency",
                "disease": node['label'],
                "red_flag": is_red_flag,
                "urgency": urgency,
                "expected": "emergent"
            })

    print(f"✓ Diseases: {stats['total_diseases']}")
    print(f"  - With urgency: {stats['diseases_with_urgency']}")
    print(f"  - Without urgency: {stats['diseases_without_urgency']}")
    print(f"  - Distribution: {stats['urgency_distribution']}")
    print(f"  - Critical issues: {len([i for i in issues if i['severity'] == 'critical'])}")

    return {
        "statistics": stats,
        "issues": issues[:20],  # Limit to first 20
        "status": "fail" if len([i for i in issues if i['severity'] == 'critical']) > 0 else "pass"
    }


def validate_medical_consistency(nodes: list, edges: list) -> dict:
    """Validate medical consistency across the graph"""
    print("\n=== VALIDATING MEDICAL CONSISTENCY ===")

    issues = []
    stats = {
        "diseases_with_symptoms": 0,
        "diseases_with_treatments": 0,
        "diseases_without_symptoms": [],
        "diseases_without_treatments": []
    }

    # Create node lookup
    node_lookup = {n['id']: n for n in nodes}

    # Create edge lookup by source
    edges_by_source = defaultdict(list)
    for edge in edges:
        edges_by_source[edge['source']].append(edge)

    # Check each disease
    disease_nodes = [n for n in nodes if n['type'] == 'Disease']
    for node in disease_nodes:
        node_id = node['id']
        outgoing = edges_by_source.get(node_id, [])

        # Check for symptoms
        has_symptoms = any(e['relationship_type'] == 'presents_with' for e in outgoing)
        if has_symptoms:
            stats["diseases_with_symptoms"] += 1
        else:
            stats["diseases_without_symptoms"].append(node['label'])

        # Check for treatments
        has_treatments = any(e['relationship_type'] == 'treated_with' for e in outgoing)
        if has_treatments:
            stats["diseases_with_treatments"] += 1
        else:
            stats["diseases_without_treatments"].append(node['label'])

    stats["diseases_without_symptoms"] = stats["diseases_without_symptoms"][:10]
    stats["diseases_without_treatments"] = stats["diseases_without_treatments"][:10]

    print(f"✓ Medical consistency:")
    print(f"  - Diseases with symptoms: {stats['diseases_with_symptoms']}")
    print(f"  - Diseases with treatments: {stats['diseases_with_treatments']}")
    print(f"  - Diseases without symptoms: {len(stats['diseases_without_symptoms'])}")
    print(f"  - Diseases without treatments: {len(stats['diseases_without_treatments'])}")

    return {
        "statistics": stats,
        "issues": issues,
        "status": "pass"
    }


def main():
    # Paths
    base_dir = Path(__file__).parent.parent.parent.parent
    phase6_dir = base_dir / "output" / "phase6"
    phase5_dir = base_dir / "output" / "phase5"
    phase4_dir = base_dir / "output" / "phase4"
    phase7_dir = base_dir / "output" / "phase7"

    nodes_file = phase6_dir / "graphrag_nodes.json"
    edges_file = phase6_dir / "graphrag_edges.json"
    red_flags_file = phase5_dir / "red_flags.json"
    urgency_criteria_file = phase4_dir / "urgency_classification_criteria.json"

    red_flag_report_file = phase7_dir / "red_flag_validation_report.json"
    urgency_report_file = phase7_dir / "urgency_validation_report.json"
    consistency_report_file = phase7_dir / "medical_consistency_report.json"

    print("=" * 80)
    print("PHASE 7.2: MEDICAL ACCURACY VALIDATION")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    nodes = load_json(nodes_file)
    edges = load_json(edges_file)
    print(f"✓ Loaded {len(nodes)} nodes and {len(edges)} edges")

    # Load source data
    red_flags_source = []
    if red_flags_file.exists():
        red_flags_source = load_json(red_flags_file)
        print(f"✓ Loaded {len(red_flags_source)} red flags from source")
    else:
        print("⚠ Red flags source file not found")

    urgency_criteria = {}
    if urgency_criteria_file.exists():
        urgency_criteria = load_json(urgency_criteria_file)
        print(f"✓ Loaded urgency criteria from source")
    else:
        print("⚠ Urgency criteria source file not found")

    # Validate red flags
    red_flag_validation = validate_red_flags(nodes, red_flags_source)

    # Validate urgency classifications
    urgency_validation = validate_urgency_classifications(nodes, urgency_criteria)

    # Validate medical consistency
    consistency_validation = validate_medical_consistency(nodes, edges)

    # Create reports
    red_flag_report = {
        "phase": "7.2",
        "title": "Red Flag Validation Report",
        "generated_at": datetime.now().isoformat(),
        "validation": red_flag_validation,
        "summary": {
            "status": red_flag_validation["status"],
            "coverage": red_flag_validation["statistics"]["coverage"],
            "critical_issues": len([i for i in red_flag_validation["issues"] if i.get("severity") == "critical"])
        }
    }

    urgency_report = {
        "phase": "7.2",
        "title": "Urgency Classification Validation Report",
        "generated_at": datetime.now().isoformat(),
        "validation": urgency_validation,
        "summary": {
            "status": urgency_validation["status"],
            "diseases_with_urgency": urgency_validation["statistics"]["diseases_with_urgency"],
            "critical_issues": len([i for i in urgency_validation["issues"] if i.get("severity") == "critical"])
        }
    }

    consistency_report = {
        "phase": "7.2",
        "title": "Medical Consistency Validation Report",
        "generated_at": datetime.now().isoformat(),
        "validation": consistency_validation,
        "summary": {
            "status": consistency_validation["status"]
        }
    }

    # Save reports
    phase7_dir.mkdir(parents=True, exist_ok=True)
    save_json(red_flag_report, red_flag_report_file)
    save_json(urgency_report, urgency_report_file)
    save_json(consistency_report, consistency_report_file)

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"\nRed Flag Validation: {red_flag_validation['status'].upper()}")
    print(f"Urgency Validation: {urgency_validation['status'].upper()}")
    print(f"Consistency Validation: {consistency_validation['status'].upper()}")
    print(f"\nReports saved:")
    print(f"  - {red_flag_report_file}")
    print(f"  - {urgency_report_file}")
    print(f"  - {consistency_report_file}")


if __name__ == "__main__":
    main()
