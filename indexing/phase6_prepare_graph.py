"""
Phase 6: Graph Preparation for Neo4j
=====================================

Converts extracted entities and relationships into Neo4j-compatible format:
- Nodes: All medical entities (diseases, symptoms, signs, treatments, tests)
- Edges: All relationships between entities
- Cypher: Import scripts for Neo4j database

Author: GraphRAG Preparation Pipeline
Date: 2025-10-23
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class GraphPreparer:
    """Prepares knowledge graph data for Neo4j ingestion."""

    def __init__(self, output_dir: str = "indexing/output/phase6"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Input paths
        self.diseases_path = Path("indexing/output/phase2/diseases.json")
        self.symptoms_path = Path("indexing/output/phase2/symptoms.json")
        self.signs_path = Path("indexing/output/phase2/signs.json")
        self.treatments_path = Path("indexing/output/phase2/treatments.json")
        self.tests_path = Path("indexing/output/phase2/diagnostic_tests.json")
        self.edges_path = Path("indexing/output/phase3/graphrag_edges.json")
        self.red_flags_path = Path("indexing/output/phase5/red_flags.json")

        # Statistics
        self.stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "node_types": {},
            "edge_types": {},
            "red_flags": 0
        }

    def _dict_to_cypher_map(self, d: Dict) -> str:
        """Convert Python dict to Cypher map literal syntax.

        Cypher maps have unquoted keys and properly escaped string values.
        Example: {id: "foo", count: 5, items: ["a", "b"]}
        """
        parts = []
        for key, value in d.items():
            # Convert key (unquoted)
            key_str = str(key)

            # Convert value based on type
            if isinstance(value, str):
                # Escape quotes and backslashes in strings
                escaped = value.replace('\\', '\\\\').replace('"', '\\"')
                value_str = f'"{escaped}"'
            elif isinstance(value, bool):
                value_str = 'true' if value else 'false'
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, list):
                # Recursively handle lists
                list_items = []
                for item in value:
                    if isinstance(item, str):
                        escaped = item.replace('\\', '\\\\').replace('"', '\\"')
                        list_items.append(f'"{escaped}"')
                    elif isinstance(item, (int, float)):
                        list_items.append(str(item))
                    elif isinstance(item, dict):
                        list_items.append(self._dict_to_cypher_map(item))
                    else:
                        list_items.append(json.dumps(item))
                value_str = '[' + ', '.join(list_items) + ']'
            elif isinstance(value, dict):
                value_str = self._dict_to_cypher_map(value)
            elif value is None:
                value_str = 'null'
            else:
                # Fallback to JSON encoding
                value_str = json.dumps(value)

            parts.append(f'{key_str}: {value_str}')

        return '{' + ', '.join(parts) + '}'

    def load_entities(self, path: Path, entity_type: str) -> List[Dict]:
        """Load entities from JSON file."""
        if not path.exists():
            print(f"Warning: {path} not found, skipping {entity_type}")
            return []

        with open(path, 'r', encoding='utf-8') as f:
            entities = json.load(f)

        print(f"Loaded {len(entities)} {entity_type} entities")
        return entities

    def convert_to_node_format(self, entity: Dict, entity_type: str) -> Dict:
        """Convert entity to Neo4j node format."""
        node = {
            "id": entity.get("entity_id") or entity.get("id"),
            "label": entity.get("name"),
            "type": entity_type,
            "properties": {}
        }

        # Add common properties
        if "name_normalized" in entity:
            node["properties"]["name_normalized"] = entity["name_normalized"]

        if "description" in entity:
            node["properties"]["description"] = entity["description"]

        if "synonyms" in entity and entity["synonyms"]:
            node["properties"]["synonyms"] = entity["synonyms"]

        # Medical codes
        if "icd_10" in entity and entity["icd_10"]:
            node["properties"]["icd_10"] = entity["icd_10"]

        if "snomed_ct" in entity and entity["snomed_ct"]:
            node["properties"]["snomed_ct"] = entity["snomed_ct"]

        # Source information
        if "chapters" in entity:
            node["properties"]["chapters"] = entity["chapters"]

        if "sections" in entity:
            node["properties"]["sections"] = entity["sections"]

        # Disease-specific properties
        if entity_type == "Disease":
            if "severity" in entity:
                node["properties"]["severity"] = entity["severity"]

            if "urgency_level" in entity:
                node["properties"]["urgency_level"] = entity["urgency_level"]

            if "urgency_source" in entity:
                node["properties"]["urgency_source"] = entity["urgency_source"]

            if "red_flag" in entity:
                node["properties"]["red_flag"] = entity["red_flag"]
                if entity["red_flag"]:
                    self.stats["red_flags"] += 1

            if "mention_count" in entity:
                node["properties"]["mention_count"] = entity["mention_count"]

        # Symptom/Sign-specific properties
        if entity_type in ["Symptom", "Sign"]:
            if "category" in entity:
                node["properties"]["category"] = entity["category"]

            if "severity" in entity:
                node["properties"]["severity"] = entity["severity"]

        # Treatment-specific properties
        if entity_type == "Treatment":
            if "type" in entity:
                node["properties"]["treatment_type"] = entity["type"]

            if "dosage" in entity:
                node["properties"]["dosage"] = entity["dosage"]

        return node

    def create_all_nodes(self) -> List[Dict]:
        """Create Neo4j nodes from all entity types."""
        all_nodes = []

        # Load and convert diseases
        diseases = self.load_entities(self.diseases_path, "Disease")
        for disease in diseases:
            node = self.convert_to_node_format(disease, "Disease")
            all_nodes.append(node)
        self.stats["node_types"]["Disease"] = len(diseases)

        # Load and convert symptoms
        symptoms = self.load_entities(self.symptoms_path, "Symptom")
        for symptom in symptoms:
            node = self.convert_to_node_format(symptom, "Symptom")
            all_nodes.append(node)
        self.stats["node_types"]["Symptom"] = len(symptoms)

        # Load and convert signs
        signs = self.load_entities(self.signs_path, "Sign")
        for sign in signs:
            node = self.convert_to_node_format(sign, "Sign")
            all_nodes.append(node)
        self.stats["node_types"]["Sign"] = len(signs)

        # Load and convert treatments
        treatments = self.load_entities(self.treatments_path, "Treatment")
        for treatment in treatments:
            node = self.convert_to_node_format(treatment, "Treatment")
            all_nodes.append(node)
        self.stats["node_types"]["Treatment"] = len(treatments)

        # Load and convert diagnostic tests
        tests = self.load_entities(self.tests_path, "DiagnosticTest")
        for test in tests:
            node = self.convert_to_node_format(test, "DiagnosticTest")
            all_nodes.append(node)
        self.stats["node_types"]["DiagnosticTest"] = len(tests)

        self.stats["nodes_created"] = len(all_nodes)
        print(f"\nTotal nodes created: {len(all_nodes)}")

        return all_nodes

    def create_all_edges(self) -> List[Dict]:
        """Create Neo4j edges from relationships."""
        if not self.edges_path.exists():
            print(f"Warning: {self.edges_path} not found")
            return []

        with open(self.edges_path, 'r', encoding='utf-8') as f:
            edges = json.load(f)

        # Convert to Neo4j format and collect statistics
        neo4j_edges = []
        for edge in edges:
            neo4j_edge = {
                "source": edge["source"],
                "target": edge["target"],
                "relationship_type": edge["relationship_type"],
                "properties": {
                    "weight": edge.get("weight", 0.5)
                }
            }

            # Add description if present
            if "description" in edge:
                neo4j_edge["properties"]["description"] = edge["description"]

            # Add metadata
            if "metadata" in edge:
                for key, value in edge["metadata"].items():
                    neo4j_edge["properties"][key] = value

            neo4j_edges.append(neo4j_edge)

            # Track edge types
            rel_type = edge["relationship_type"]
            self.stats["edge_types"][rel_type] = self.stats["edge_types"].get(rel_type, 0) + 1

        self.stats["edges_created"] = len(neo4j_edges)
        print(f"\nTotal edges created: {len(neo4j_edges)}")

        return neo4j_edges

    def generate_cypher_import(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """Generate Cypher script for Neo4j import."""
        cypher_lines = []

        # Header
        cypher_lines.append("// GraphRAG Knowledge Graph Import Script")
        cypher_lines.append(f"// Generated: {datetime.now().isoformat()}")
        cypher_lines.append("// Source: Wills Eye Manual (7th Edition)")
        cypher_lines.append("")
        cypher_lines.append("// Create constraints and indexes")
        cypher_lines.append("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;")
        cypher_lines.append("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);")
        cypher_lines.append("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.label);")
        cypher_lines.append("")

        # Node creation (batch by type for efficiency)
        cypher_lines.append("// Create nodes by type")
        for node_type in self.stats["node_types"].keys():
            cypher_lines.append(f"\n// Create {node_type} nodes")
            type_nodes = [n for n in nodes if n["type"] == node_type]

            # Batch nodes (50 per batch for readability)
            batch_size = 50
            for i in range(0, len(type_nodes), batch_size):
                batch = type_nodes[i:i+batch_size]
                cypher_lines.append("UNWIND [")

                for j, node in enumerate(batch):
                    props = {
                        "id": node["id"],
                        "label": node["label"],
                        "type": node["type"],
                        **node["properties"]
                    }
                    # Convert to Cypher map syntax (unquoted keys, escaped values)
                    props_cypher = self._dict_to_cypher_map(props)
                    comma = "," if j < len(batch) - 1 else ""
                    cypher_lines.append(f"  {props_cypher}{comma}")

                cypher_lines.append("] AS nodeData")
                cypher_lines.append("CREATE (e:Entity)")
                cypher_lines.append("SET e = nodeData;")
                cypher_lines.append("")

        # Relationship creation (compact format)
        cypher_lines.append("\n// Create relationships")
        for rel_type in self.stats["edge_types"].keys():
            type_edges = [e for e in edges if e["relationship_type"] == rel_type]
            cypher_lines.append(f"\n// Create {rel_type} relationships ({len(type_edges)} total)")

            # Batch edges
            batch_size = 100
            for i in range(0, len(type_edges), batch_size):
                batch = type_edges[i:i+batch_size]
                cypher_lines.append("UNWIND [")

                for j, edge in enumerate(batch):
                    edge_data = {
                        "source": edge["source"],
                        "target": edge["target"],
                        "properties": edge["properties"]
                    }
                    # Convert to Cypher map syntax
                    edge_cypher = self._dict_to_cypher_map(edge_data)
                    comma = "," if j < len(batch) - 1 else ""
                    cypher_lines.append(f"  {edge_cypher}{comma}")

                cypher_lines.append("] AS relData")
                cypher_lines.append("MATCH (source:Entity {id: relData.source})")
                cypher_lines.append("MATCH (target:Entity {id: relData.target})")
                rel_type_safe = rel_type.upper().replace(" ", "_")
                cypher_lines.append(f"CREATE (source)-[r:{rel_type_safe}]->(target)")
                cypher_lines.append("SET r = relData.properties;")
                cypher_lines.append("")

        return "\n".join(cypher_lines)

    def generate_csv_export(self, nodes: List[Dict], edges: List[Dict]):
        """Generate CSV files for Neo4j bulk import."""
        import csv

        # Nodes CSV
        nodes_csv = self.output_dir / "nodes.csv"
        with open(nodes_csv, 'w', newline='', encoding='utf-8') as f:
            # Collect all possible property keys
            all_keys = set()
            for node in nodes:
                all_keys.update(node["properties"].keys())

            fieldnames = ["id:ID", "label", ":LABEL"] + [f"properties.{k}" for k in sorted(all_keys)]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for node in nodes:
                row = {
                    "id:ID": node["id"],
                    "label": node["label"],
                    ":LABEL": "Entity"
                }
                for k, v in node["properties"].items():
                    if isinstance(v, (list, dict)):
                        row[f"properties.{k}"] = json.dumps(v)
                    else:
                        row[f"properties.{k}"] = v
                writer.writerow(row)

        print(f"Created nodes CSV: {nodes_csv}")

        # Edges CSV
        edges_csv = self.output_dir / "relationships.csv"
        with open(edges_csv, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [":START_ID", ":END_ID", ":TYPE", "weight", "description"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for edge in edges:
                row = {
                    ":START_ID": edge["source"],
                    ":END_ID": edge["target"],
                    ":TYPE": edge["relationship_type"].upper().replace(" ", "_"),
                    "weight": edge["properties"].get("weight", 0.5),
                    "description": edge["properties"].get("description", "")
                }
                writer.writerow(row)

        print(f"Created edges CSV: {edges_csv}")

    def generate_report(self) -> Dict:
        """Generate Phase 6 report."""
        report = {
            "phase": 6,
            "title": "Graph Preparation for Neo4j",
            "generated_at": datetime.now().isoformat(),
            "statistics": self.stats,
            "outputs": {
                "nodes_json": str(self.output_dir / "graphrag_nodes.json"),
                "edges_json": str(self.output_dir / "graphrag_edges.json"),
                "cypher_script": str(self.output_dir / "neo4j_import.cypher"),
                "nodes_csv": str(self.output_dir / "nodes.csv"),
                "edges_csv": str(self.output_dir / "relationships.csv")
            },
            "validation": {
                "nodes_created": self.stats["nodes_created"] > 0,
                "edges_created": self.stats["edges_created"] > 0,
                "red_flags_present": self.stats["red_flags"] > 0
            }
        }

        return report

    def run(self):
        """Execute Phase 6 graph preparation pipeline."""
        print("=" * 80)
        print("Phase 6: Graph Preparation for Neo4j")
        print("=" * 80)

        # Create nodes
        print("\n[1/5] Creating Neo4j nodes...")
        nodes = self.create_all_nodes()

        # Create edges
        print("\n[2/5] Creating Neo4j edges...")
        edges = self.create_all_edges()

        # Save JSON outputs
        print("\n[3/5] Saving JSON outputs...")
        nodes_file = self.output_dir / "graphrag_nodes.json"
        with open(nodes_file, 'w', encoding='utf-8') as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)
        print(f"Saved: {nodes_file}")

        edges_file = self.output_dir / "graphrag_edges.json"
        with open(edges_file, 'w', encoding='utf-8') as f:
            json.dump(edges, f, indent=2, ensure_ascii=False)
        print(f"Saved: {edges_file}")

        # Generate Cypher script
        print("\n[4/5] Generating Cypher import script...")
        cypher = self.generate_cypher_import(nodes, edges)
        cypher_file = self.output_dir / "neo4j_import.cypher"
        with open(cypher_file, 'w', encoding='utf-8') as f:
            f.write(cypher)
        print(f"Saved: {cypher_file}")

        # Generate CSV export
        print("\n[5/5] Generating CSV export...")
        self.generate_csv_export(nodes, edges)

        # Generate report
        report = self.generate_report()
        report_file = self.output_dir / "phase6_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\nSaved report: {report_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("Phase 6 Summary")
        print("=" * 80)
        print(f"Nodes created: {self.stats['nodes_created']}")
        print(f"Edges created: {self.stats['edges_created']}")
        print(f"Red flags: {self.stats['red_flags']}")
        print("\nNode types:")
        for node_type, count in self.stats['node_types'].items():
            print(f"  - {node_type}: {count}")
        print("\nEdge types (top 10):")
        sorted_edges = sorted(self.stats['edge_types'].items(), key=lambda x: x[1], reverse=True)
        for edge_type, count in sorted_edges[:10]:
            print(f"  - {edge_type}: {count}")

        print("\n" + "=" * 80)
        print("Phase 6 complete!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Review outputs in indexing/output/phase6/")
        print("  2. Run embedding preparation (see embedding_project/)")
        print("  3. Import to Neo4j using neo4j_import.cypher")
        print("  4. Move to Phase 7: Validation")


if __name__ == "__main__":
    preparer = GraphPreparer()
    preparer.run()
