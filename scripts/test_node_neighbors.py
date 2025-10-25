#!/usr/bin/env python3
"""Test script for get_node_neighbors fix"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def test_node_neighbors():
    """Test get_node_neighbors with Person node ID as string"""
    print("\n" + "="*60)
    print("TEST: get_node_neighbors('Person', '400')")
    print("="*60)
    
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j")
        
        # Test with string ID
        print("\nCalling get_node_neighbors('Person', '400', limit=5)...")
        result = query_service.get_node_neighbors('Person', '400', limit=5)
        
        if result:
            print(f"\n✓ SUCCESS: Found {len(result)} relationship types")
            for rel_type, data in result.items():
                print(f"\n  [{rel_type}] → {data['neighborType']}")
                print(f"    Total: {data['totalCount']}")
                print(f"    Sample neighbors: {min(5, len(data['neighbors']))}")
                for i, neighbor in enumerate(data['neighbors'][:3], 1):
                    print(f"      {i}. {neighbor}")
        else:
            print("\n✗ FAILED: No neighbors found (empty dict returned)")
            print("   This means either:")
            print("   - Person with id=400 doesn't exist in DB")
            print("   - Person exists but has no relationships")
            
            # Try to verify the person exists
            print("\n  Checking if Person with id=400 exists...")
            check_query = """
            MATCH (p:Person {id: 400})
            RETURN p.id as id, p.firstLastName as name, p.club as club
            """
            person_check = neo4j_client.execute_read_query(check_query, {})
            
            if person_check:
                print(f"  ✓ Person exists: {person_check[0]}")
                print("  → Issue: Person exists but has no relationships")
            else:
                print("  ✗ Person with id=400 NOT found in database")
                print("  → Try a different ID or check database contents")
        
        return bool(result)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    success = test_node_neighbors()
    sys.exit(0 if success else 1)
