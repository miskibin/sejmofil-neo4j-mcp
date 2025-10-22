#!/usr/bin/env python3
"""
Database exploration script for Sejmofil Neo4j database
This script connects to the Neo4j database and provides basic exploration functionality.
"""

import sys
import os
from pathlib import Path

# Add the sejmofil_mcp package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.config import settings


def connect_to_database():
    """Connect to the Neo4j database"""
    try:
        neo4j_client.connect()
        print("✅ Successfully connected to Neo4j database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        return False


def get_database_info():
    """Get basic database information"""
    print("\n📊 DATABASE INFORMATION")
    print("=" * 50)

    # Get node counts by label
    print("\n🔢 NODE COUNTS BY LABEL:")
    node_query = """
    CALL db.labels() YIELD label
    CALL {
        WITH label
        MATCH (n)
        WHERE label IN labels(n)
        RETURN count(n) as count
    }
    RETURN label, count
    ORDER BY count DESC
    """

    try:
        results = neo4j_client.execute_read_query(node_query)
        for result in results:
            print(f"  {result['label']}: {result['count']:,}")
    except Exception as e:
        print(f"Error getting node counts: {e}")

    # Get relationship counts by type
    print("\n🔗 RELATIONSHIP COUNTS BY TYPE:")
    rel_query = """
    CALL db.relationshipTypes() YIELD relationshipType
    CALL {
        WITH relationshipType
        MATCH ()-[r]-()
        WHERE type(r) = relationshipType
        RETURN count(r) as count
    }
    RETURN relationshipType, count
    ORDER BY count DESC
    """

    try:
        results = neo4j_client.execute_read_query(rel_query)
        for result in results:
            print(f"  {result['relationshipType']}: {result['count']:,}")
    except Exception as e:
        print(f"Error getting relationship counts: {e}")


def sample_nodes(label, limit=5):
    """Sample nodes of a specific label"""
    print(f"\n📋 SAMPLE {label.upper()} NODES (first {limit}):")
    print("-" * 50)

    query = f"""
    MATCH (n:{label})
    RETURN n
    LIMIT {limit}
    """

    try:
        results = neo4j_client.execute_read_query(query)
        for i, result in enumerate(results, 1):
            node = result['n']
            print(f"{i}. Properties: {dict(node)}")
    except Exception as e:
        print(f"Error sampling {label} nodes: {e}")


def sample_relationships(relationship_type, limit=5):
    """Sample relationships of a specific type"""
    print(f"\n🔗 SAMPLE {relationship_type.upper()} RELATIONSHIPS (first {limit}):")
    print("-" * 50)

    query = f"""
    MATCH (a)-[r:{relationship_type}]->(b)
    RETURN a, r, b
    LIMIT {limit}
    """

    try:
        results = neo4j_client.execute_read_query(query)
        for i, result in enumerate(results, 1):
            a, r, b = result['a'], result['r'], result['b']
            print(f"{i}. {dict(a)} -[{dict(r)}]-> {dict(b)}")
    except Exception as e:
        print(f"Error sampling {relationship_type} relationships: {e}")


def get_schema_details():
    """Get detailed schema information"""
    print("\n📋 DETAILED SCHEMA INFORMATION")
    print("=" * 50)

    # Get all labels and their properties
    labels_query = """
    CALL db.labels() YIELD label
    CALL {
        WITH label
        MATCH (n)
        WHERE label IN labels(n)
        UNWIND keys(n) as key
        RETURN collect(DISTINCT key) as properties
    }
    RETURN label, properties
    ORDER BY label
    """

    print("\n🏷️  NODE LABELS AND PROPERTIES:")
    try:
        results = neo4j_client.execute_read_query(labels_query)
        for result in results:
            label = result['label']
            properties = result['properties']
            print(f"  {label}: {', '.join(properties)}")
    except Exception as e:
        print(f"Error getting schema details: {e}")


def main():
    """Main function"""
    print("🔍 SEJMOFIL DATABASE EXPLORATION")
    print("=" * 50)
    print(f"Host: {settings.NEO4J_HOST}")
    print(f"User: {settings.NEO4J_USER}")

    if not connect_to_database():
        return

    try:
        get_database_info()

        # Sample key node types
        key_labels = ['Person', 'Club', 'Print', 'Process', 'Topic', 'Committee']
        for label in key_labels:
            sample_nodes(label)

        # Sample key relationship types
        key_relationships = ['BELONGS_TO', 'AUTHORED', 'REFERS_TO', 'HAS', 'SAID']
        for rel_type in key_relationships:
            sample_relationships(rel_type)

        get_schema_details()

    finally:
        neo4j_client.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    main()