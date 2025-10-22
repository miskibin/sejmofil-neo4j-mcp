#!/usr/bin/env python3
"""
Debug queries for Sejmofil Neo4j database
This script contains various useful queries for exploring and debugging the database.
"""

import sys
import os
from pathlib import Path

# Add the sejmofil_mcp package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.config import settings

def run_debug_queries():
    """Run various debug queries to test database connectivity and data."""

    print("=== Sejmofil Neo4j Database Debug Queries ===\n")

    # Connect to database first
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j database")
    except Exception as e:
        print(f"✗ Failed to connect to Neo4j: {e}")
        return False

    try:
        # Test basic connectivity
        print("\n1. Testing database connection...")
        result = neo4j_client.execute_read_query("MATCH () RETURN count(*) as node_count")
        node_count = result[0]['node_count']
        print(f"   ✓ Connected successfully. Total nodes: {node_count:,}")

        # Get node label counts
        print("\n2. Node label counts:")
        result = neo4j_client.execute_read_query("""
            CALL db.labels() YIELD label
            CALL {
                WITH label
                MATCH (n)
                WHERE label IN labels(n)
                RETURN count(n) as count
            }
            RETURN label, count
            ORDER BY count DESC
        """)

        for record in result:
            print(f"   {record['label']}: {record['count']:,}")

        # Get relationship type counts
        print("\n3. Relationship type counts:")
        result = neo4j_client.execute_read_query("""
            CALL db.relationshipTypes() YIELD relationshipType
            CALL {
                WITH relationshipType
                MATCH ()-[r]-()
                WHERE type(r) = relationshipType
                RETURN count(r) as count
            }
            RETURN relationshipType, count
            ORDER BY count DESC
        """)

        for record in result:
            print(f"   {record['relationshipType']}: {record['count']:,}")

        # Sample data from key nodes
        print("\n4. Sample Person nodes:")
        result = neo4j_client.execute_read_query("""
            MATCH (p:Person)
            RETURN p.firstLastName as name, p.club as party, p.districtName as district
            LIMIT 5
        """)

        for record in result:
            print(f"   {record['name']} ({record['party']}) - {record['district']}")

        print("\n5. Sample Print nodes:")
        result = neo4j_client.execute_read_query("""
            MATCH (p:Print)
            RETURN p.number as number, p.title as title
            ORDER BY p.documentDate DESC
            LIMIT 3
        """)

        for record in result:
            title = record['title'][:60] + "..." if len(record['title']) > 60 else record['title']
            print(f"   Print {record['number']}: {title}")

        print("\n6. Recent speeches:")
        result = neo4j_client.execute_read_query("""
            MATCH (p:Person)-[r:SAID]->(s:Statement)
            RETURN p.firstLastName as speaker, s.statement_official_topic as topic, r.date as date
            ORDER BY r.date DESC
            LIMIT 3
        """)

        for record in result:
            topic = record['topic'][:50] + "..." if record['topic'] and len(record['topic']) > 50 else record['topic']
            print(f"   {record['speaker']} on {record['date']}: {topic}")

        print("\n7. Active committees:")
        result = neo4j_client.execute_read_query("""
            MATCH (c:Committee)
            OPTIONAL MATCH (c)<-[:BELONGS_TO]-(p:Person)
            RETURN c.name as committee, count(p) as members
            ORDER BY members DESC
            LIMIT 5
        """)

        for record in result:
            print(f"   {record['committee']}: {record['members']} members")

        print("\n8. Political parties:")
        result = neo4j_client.execute_read_query("""
            MATCH (c:Club)
            OPTIONAL MATCH (c)<-[:BELONGS_TO]-(p:Person)
            RETURN c.name as party, count(p) as members
            ORDER BY members DESC
        """)

        for record in result:
            print(f"   {record['party']}: {record['members']} members")

        print("\n✓ All debug queries completed successfully!")

    except Exception as e:
        print(f"✗ Error running debug queries: {e}")
        return False
    finally:
        neo4j_client.close()

    return True

if __name__ == "__main__":
    success = run_debug_queries()
    sys.exit(0 if success else 1)