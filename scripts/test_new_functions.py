#!/usr/bin/env python3
"""
Test new generic functions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")


def test_search_prints():
    """Test search_prints_by_query with different filters"""
    print("\n" + "="*80)
    print("TEST: search_prints_by_query")
    print("="*80)
    
    neo4j_client.connect()
    
    try:
        # Test 1: Search all prints
        print("\n1. Search all prints about 'podatki':")
        results = query_service.search_prints_by_query("podatki", limit=3, status_filter=None)
        print(f"   Found {len(results)} results")
        for r in results:
            print(f"   - Print {r.number}: {r.title[:60]}")
        
        # Test 2: Search active only
        print("\n2. Search ACTIVE prints about 'podatki':")
        results = query_service.search_prints_by_query("podatki", limit=3, status_filter='active')
        print(f"   Found {len(results)} results")
        for r in results:
            print(f"   - Print {r.number}: {r.title[:60]} (Stage: {r.currentStage})")
        
        # Test 3: Search finished only
        print("\n3. Search FINISHED prints about 'podatki':")
        results = query_service.search_prints_by_query("podatki", limit=3, status_filter='finished')
        print(f"   Found {len(results)} results")
        for r in results:
            print(f"   - Print {r.number}: {r.title[:60]} (Stage: {r.currentStage})")
            
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()


def test_explore_node():
    """Test generic node neighbor exploration"""
    print("\n" + "="*80)
    print("TEST: get_node_neighbors")
    print("="*80)
    
    neo4j_client.connect()
    
    try:
        # Test 1: Explore a Person node
        print("\n1. Explore Person node (first MP):")
        # Get first person
        query = "MATCH (p:Person) RETURN p.id as id, p.firstLastName as name LIMIT 1"
        person = neo4j_client.execute_read_query(query)[0]
        print(f"   Testing with: {person['name']} (ID: {person['id']})")
        
        neighbors = query_service.get_node_neighbors('Person', str(person['id']), limit=5)
        print(f"   Found {len(neighbors)} relationship types:")
        for rel_type, data in neighbors.items():
            print(f"     - {rel_type}: {data['totalCount']} {data['neighborType']} nodes")
        
        # Test 2: Explore a Print node
        print("\n2. Explore Print node:")
        query = "MATCH (p:Print) RETURN p.number as number, p.title as title LIMIT 1"
        print_node = neo4j_client.execute_read_query(query)[0]
        print(f"   Testing with: Print {print_node['number']}")
        
        neighbors = query_service.get_node_neighbors('Print', print_node['number'], limit=5)
        print(f"   Found {len(neighbors)} relationship types:")
        for rel_type, data in neighbors.items():
            print(f"     - {rel_type}: {data['totalCount']} {data['neighborType']} nodes")
        
        # Test 3: Explore a Topic node
        print("\n3. Explore Topic node:")
        query = "MATCH (t:Topic) RETURN t.name as name LIMIT 1"
        topic = neo4j_client.execute_read_query(query)[0]
        print(f"   Testing with: Topic '{topic['name']}'")
        
        neighbors = query_service.get_node_neighbors('Topic', topic['name'], limit=5)
        print(f"   Found {len(neighbors)} relationship types:")
        for rel_type, data in neighbors.items():
            print(f"     - {rel_type}: {data['totalCount']} {data['neighborType']} nodes")
            
        # Test 4: Explore a Club node
        print("\n4. Explore Club node:")
        query = "MATCH (c:Club) WHERE c.name CONTAINS 'PiS' RETURN c.name as name LIMIT 1"
        club = neo4j_client.execute_read_query(query)[0]
        print(f"   Testing with: Club '{club['name']}'")
        
        neighbors = query_service.get_node_neighbors('Club', club['name'], limit=5)
        print(f"   Found {len(neighbors)} relationship types:")
        for rel_type, data in neighbors.items():
            print(f"     - {rel_type}: {data['totalCount']} {data['neighborType']} nodes")
            
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()


def test_terminal_stages():
    """Verify terminal stage detection works"""
    print("\n" + "="*80)
    print("TEST: Terminal Stage Detection")
    print("="*80)
    
    neo4j_client.connect()
    
    try:
        # Check processes with PUBLICATION type
        query = """
        MATCH (process:Process)-[:HAS]->(stage:Stage)
        WHERE stage.type = 'PUBLICATION'
        WITH process, stage
        ORDER BY stage.date DESC
        WITH process, COLLECT(stage)[0] as latestStage
        RETURN process.number as processNumber, latestStage.stageName as stageName,
               latestStage.type as type
        LIMIT 3
        """
        
        print("\n1. Processes with PUBLICATION type stage:")
        results = neo4j_client.execute_read_query(query)
        for r in results:
            print(f"   Process {r['processNumber']}: {r['stageName']} (type: {r['type']})")
        
        # Check status using new logic
        query = """
        MATCH (process:Process)-[:HAS]->(stage:Stage)
        WITH process, stage
        ORDER BY stage.date DESC, stage.number DESC
        WITH process, COLLECT(stage)[0] as latestStage
        WHERE latestStage.type IN ['PUBLICATION', 'WITHDRAWAL']
        RETURN 
          process.number as processNumber,
          latestStage.stageName as stageName,
          latestStage.type as type,
          'finished' as status
        LIMIT 3
        """
        
        print("\n2. Finished processes (using type-based detection):")
        results = neo4j_client.execute_read_query(query)
        for r in results:
            print(f"   Process {r['processNumber']}: {r['stageName']} (type: {r['type']}, status: {r['status']})")
            
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING NEW GENERIC MCP FUNCTIONS")
    print("="*80)
    
    test_search_prints()
    test_explore_node()
    test_terminal_stages()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
