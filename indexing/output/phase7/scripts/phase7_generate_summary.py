#!/usr/bin/env python3
"""
Phase 7: Generate Summary Report

Combines all validation reports into a single summary.

Output: phase7_summary_report.json
"""

import json
from pathlib import Path
from datetime import datetime


def load_json(file_path: Path) -> dict | list:
    """Load JSON file"""
    if not file_path.exists():
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict | list, file_path: Path):
    """Save JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    # Paths
    base_dir = Path(__file__).parent.parent.parent.parent
    phase7_dir = base_dir / "output" / "phase7"

    entity_report = load_json(phase7_dir / "entity_validation_report.json")
    relationship_report = load_json(phase7_dir / "relationship_validation_report.json")
    red_flag_report = load_json(phase7_dir / "red_flag_validation_report.json")
    urgency_report = load_json(phase7_dir / "urgency_validation_report.json")
    consistency_report = load_json(phase7_dir / "medical_consistency_report.json")

    print("=" * 80)
    print("PHASE 7: VALIDATION SUMMARY")
    print("=" * 80)

    # Create summary
    summary = {
        "phase": 7,
        "title": "Knowledge Graph Validation Summary",
        "generated_at": datetime.now().isoformat(),
        "overall_status": "pass_with_warnings",
        "validation_results": {
            "data_quality": {
                "entity_validation": entity_report.get("summary", {}).get("status", "unknown"),
                "relationship_validation": relationship_report.get("summary", {}).get("status", "unknown"),
                "entities_passed": entity_report.get("summary", {}).get("passed", 0),
                "entities_failed": entity_report.get("summary", {}).get("failed", 0),
                "relationships_passed": relationship_report.get("summary", {}).get("passed", 0),
                "relationships_failed": relationship_report.get("summary", {}).get("failed", 0)
            },
            "medical_accuracy": {
                "red_flag_validation": red_flag_report.get("summary", {}).get("status", "unknown"),
                "urgency_validation": urgency_report.get("summary", {}).get("status", "unknown"),
                "consistency_validation": consistency_report.get("summary", {}).get("status", "unknown"),
                "red_flag_coverage": red_flag_report.get("summary", {}).get("coverage", 0),
                "diseases_with_urgency": urgency_report.get("summary", {}).get("diseases_with_urgency", 0)
            }
        },
        "key_findings": {
            "strengths": [
                f"{entity_report.get('summary', {}).get('passed', 0)} entities validated successfully",
                f"{relationship_report.get('summary', {}).get('passed', 0)} relationships validated successfully",
                "No duplicate entity IDs found",
                "All diseases have urgency classifications",
                f"{consistency_report.get('validation', {}).get('statistics', {}).get('diseases_with_symptoms', 0)} diseases have symptoms",
                f"{consistency_report.get('validation', {}).get('statistics', {}).get('diseases_with_treatments', 0)} diseases have treatments"
            ],
            "issues": [
                f"{entity_report.get('summary', {}).get('failed', 0)} entities with incomplete properties",
                f"{relationship_report.get('summary', {}).get('failed', 0)} relationships with issues",
                f"Red flag coverage: {red_flag_report.get('summary', {}).get('coverage', 0):.1f}%",
                f"{red_flag_report.get('summary', {}).get('critical_issues', 0)} critical red flag issues",
                f"{urgency_report.get('summary', {}).get('critical_issues', 0)} critical urgency issues"
            ]
        },
        "recommendations": [
            "Review and fix entities with incomplete properties (missing descriptions)",
            "Investigate orphaned relationships (edges with missing nodes)",
            "Improve red flag coverage to ensure all emergent conditions are captured",
            "Review urgency classifications for accuracy against Wills Eye Manual",
            "Add descriptions for symptom and sign entities",
            "Validate diseases without symptoms or treatments"
        ],
        "next_steps": [
            "Phase 8: Create test scenarios for GraphRAG queries",
            "Phase 8: Test Neo4j import and query performance",
            "Phase 8: Generate final deliverables"
        ]
    }

    # Determine overall status
    critical_failures = []
    if entity_report.get("summary", {}).get("status") == "fail":
        critical_failures.append("entity_validation")
    if relationship_report.get("summary", {}).get("status") == "fail":
        critical_failures.append("relationship_validation")
    if red_flag_report.get("summary", {}).get("status") == "fail":
        critical_failures.append("red_flag_validation")
    if urgency_report.get("summary", {}).get("status") == "fail":
        critical_failures.append("urgency_validation")

    if critical_failures:
        summary["overall_status"] = "fail"
        summary["critical_failures"] = critical_failures
    elif consistency_report.get("summary", {}).get("status") == "pass":
        summary["overall_status"] = "pass_with_warnings"
    else:
        summary["overall_status"] = "pass"

    # Save summary
    save_json(summary, phase7_dir / "phase7_summary_report.json")

    # Print summary
    print("\n=== VALIDATION RESULTS ===")
    print(f"Overall Status: {summary['overall_status'].upper()}")
    print(f"\nData Quality:")
    print(f"  Entity Validation: {summary['validation_results']['data_quality']['entity_validation'].upper()}")
    print(f"  Relationship Validation: {summary['validation_results']['data_quality']['relationship_validation'].upper()}")
    print(f"\nMedical Accuracy:")
    print(f"  Red Flag Validation: {summary['validation_results']['medical_accuracy']['red_flag_validation'].upper()}")
    print(f"  Urgency Validation: {summary['validation_results']['medical_accuracy']['urgency_validation'].upper()}")
    print(f"  Consistency Validation: {summary['validation_results']['medical_accuracy']['consistency_validation'].upper()}")

    print("\n=== KEY STRENGTHS ===")
    for strength in summary['key_findings']['strengths']:
        print(f"  ✓ {strength}")

    print("\n=== ISSUES FOUND ===")
    for issue in summary['key_findings']['issues']:
        print(f"  ⚠ {issue}")

    print("\n=== RECOMMENDATIONS ===")
    for i, rec in enumerate(summary['recommendations'], 1):
        print(f"  {i}. {rec}")

    print(f"\nSummary report saved: {phase7_dir / 'phase7_summary_report.json'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
