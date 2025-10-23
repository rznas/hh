"""Import GraphRAG knowledge graph into Neo4j using Python driver."""

import argparse
import json
import re
from neo4j import GraphDatabase
from pathlib import Path


class Neo4jImporter:
    def __init__(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            username: Neo4j username
            password: Neo4j password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close Neo4j connection."""
        self.driver.close()

    def clear_database(self):
        """Clear all nodes, relationships, constraints and indexes from database."""
        print("Clearing database...")
        with self.driver.session() as session:
            # Drop all constraints
            print("Dropping constraints...")
            result = session.run("SHOW CONSTRAINTS")
            for record in result:
                constraint_name = record.get('name')
                if constraint_name:
                    try:
                        session.run(f"DROP CONSTRAINT {constraint_name}")
                    except Exception as e:
                        print(f"Warning: Could not drop constraint {constraint_name}: {e}")

            # Drop all indexes
            print("Dropping indexes...")
            result = session.run("SHOW INDEXES")
            for record in result:
                index_name = record.get('name')
                if index_name and not index_name.startswith('constraint_'):
                    try:
                        session.run(f"DROP INDEX {index_name}")
                    except Exception as e:
                        print(f"Warning: Could not drop index {index_name}: {e}")

            # Delete all nodes and relationships
            print("Deleting all nodes and relationships...")
            session.run("MATCH (n) DETACH DELETE n")

        print("Database cleared successfully")

    def execute_cypher_file(self, filepath: str):
        """Execute Cypher statements from file.

        Args:
            filepath: Path to .cypher file
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        print(f"Reading Cypher file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove comments
        lines = []
        for line in content.split('\n'):
            if not line.strip().startswith('//'):
                lines.append(line)

        cypher_content = '\n'.join(lines)

        # Split by semicolons to get individual statements
        # This is a simple split that works for our generated file
        statements = [stmt.strip() for stmt in cypher_content.split(';') if stmt.strip()]

        print(f"Found {len(statements)} Cypher statements")
        print(f"Executing statements (this may take a while)...")

        # Execute each statement
        with self.driver.session() as session:
            for i, statement in enumerate(statements, 1):
                try:
                    session.run(statement)
                    if i % 10 == 0:
                        print(f"Executed {i}/{len(statements)} statements...")
                except Exception as e:
                    print(f"Error executing statement {i}:")
                    print(f"Statement preview: {statement[:200]}...")
                    print(f"Error: {e}")
                    raise

        print("Import completed successfully!")

    def verify_import(self):
        """Verify import by counting nodes and relationships."""
        print("\nVerifying import...")

        with self.driver.session() as session:
            # Count nodes by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """)

            print("\nNodes by type:")
            total_nodes = 0
            for record in result:
                print(f"  {record['label']}: {record['count']}")
                total_nodes += record['count']
            print(f"  Total nodes: {total_nodes}")

            # Count relationships by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """)

            print("\nRelationships by type:")
            total_rels = 0
            for record in result:
                print(f"  {record['type']}: {record['count']}")
                total_rels += record['count']
            print(f"  Total relationships: {total_rels}")


def main():
    """Main import function."""
    parser = argparse.ArgumentParser(description='Import GraphRAG data into Neo4j')
    parser.add_argument('--uri', default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--username', default='neo4j', help='Neo4j username')
    parser.add_argument('--password', default='password', help='Neo4j password')
    parser.add_argument('--file', default='output/phase6/neo4j_import.cypher', help='Cypher file to import')
    parser.add_argument('--clear', action='store_true', help='Clear database before import')
    parser.add_argument('--no-verify', action='store_true', help='Skip verification after import')

    args = parser.parse_args()

    # Create importer
    importer = Neo4jImporter(args.uri, args.username, args.password)

    try:
        # Optional: Clear existing data
        if args.clear:
            print("WARNING: Clearing all existing data in the Neo4j database!")
            importer.clear_database()

        # Execute import
        importer.execute_cypher_file(args.file)

        # Verify
        if not args.no_verify:
            importer.verify_import()

    except Exception as e:
        print(f"Import failed: {e}")
        raise
    finally:
        importer.close()
        print("\nConnection closed")


if __name__ == "__main__":
    main()
