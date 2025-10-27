#!/usr/bin/env python3
"""Test script to investigate search_prints issue with 'związki partnerskie'"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def check_print_1457():
    """Check if print 1457 exists and what it contains"""
    print("\n" + "="*60)
    print("TEST 1: Check Print 1457 Details")
    print("="*60)
    
    query = """
    MATCH (print:Print {number: '1457'})
    OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
    
    RETURN 
      print.number as number,
      print.title as title,
      print.summary as summary,
      print.processPrint as processPrint,
      COLLECT(DISTINCT topic.name) as topics
    """
    
    results = neo4j_client.execute_read_query(query, {})
    
    if results:
        r = results[0]
        print(f"\n✓ Print 1457 EXISTS")
        print(f"  Number: {r['number']}")
        print(f"  Title: {r['title']}")
        print(f"  Summary: {r['summary'][:200] if r['summary'] else 'NO SUMMARY'}...")
        print(f"  ProcessPrint: {r['processPrint']}")
        print(f"  Topics: {r['topics']}")
        
        # Check if it passes the filter
        if r['processPrint'] and r['number'] in r['processPrint']:
            print(f"\n  ✓ PASSES filter: print.number IN print.processPrint")
        else:
            print(f"\n  ✗ FAILS filter: print.number IN print.processPrint")
            print(f"     Number '{r['number']}' NOT IN {r['processPrint']}")
        
        return r
    else:
        print("\n✗ Print 1457 NOT FOUND")
        return None


def test_vector_search():
    """Test vector search for 'związki partnerskie'"""
    print("\n" + "="*60)
    print("TEST 2: Vector Search for 'związki partnerskie'")
    print("="*60)
    
    query = """
    CALL db.index.vector.queryNodes('printEmbeddingIndex', 10, $embedding)
    YIELD node as print, score
    WHERE print.summary IS NOT NULL
      AND print.number IN print.processPrint
    
    RETURN 
      print.number as number,
      print.title as title,
      print.summary as summary,
      score
    ORDER BY score ASC
    LIMIT 10
    """
    
    from sejmofil_mcp.embeddings import embeddings_service
    
    if not embeddings_service.is_available():
        print("✗ Embeddings service not available - skipping vector search test")
        return []
    
    embedding = embeddings_service.generate_embedding("związki partnerskie")
    results = neo4j_client.execute_read_query(query, {"embedding": embedding})
    
    print(f"\n✓ Vector search returned {len(results)} results")
    
    found_1457 = False
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Print {r['number']} (score: {r['score']:.4f})")
        print(f"   Title: {r['title'][:80]}")
        if r['number'] == '1457':
            found_1457 = True
            print("   >>> THIS IS PRINT 1457! <<<")
    
    if not found_1457:
        print("\n✗ Print 1457 NOT in vector search results")
    
    return results


def test_fulltext_search():
    """Test fulltext search for 'związki partnerskie'"""
    print("\n" + "="*60)
    print("TEST 3: Fulltext Search for 'związki partnerskie'")
    print("="*60)
    
    query = """
    CALL db.index.fulltext.queryNodes("print_content", $query) 
    YIELD node as print, score
    WHERE print.summary IS NOT NULL
      AND print.number IN print.processPrint
    
    RETURN 
      print.number as number,
      print.title as title,
      print.summary as summary,
      score
    ORDER BY score DESC
    LIMIT 10
    """
    
    results = neo4j_client.execute_read_query(query, {"query": "związki partnerskie"})
    
    print(f"\n✓ Fulltext search returned {len(results)} results")
    
    found_1457 = False
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Print {r['number']} (score: {r['score']:.4f})")
        print(f"   Title: {r['title'][:80]}")
        if r['number'] == '1457':
            found_1457 = True
            print("   >>> THIS IS PRINT 1457! <<<")
    
    if not found_1457:
        print("\n✗ Print 1457 NOT in fulltext search results")
    
    return results


def test_search_without_filter():
    """Test searches WITHOUT the processPrint filter"""
    print("\n" + "="*60)
    print("TEST 4: Search WITHOUT processPrint filter")
    print("="*60)
    
    query = """
    CALL db.index.fulltext.queryNodes("print_content", $query) 
    YIELD node as print, score
    WHERE print.summary IS NOT NULL
    
    RETURN 
      print.number as number,
      print.title as title,
      print.processPrint as processPrint,
      score
    ORDER BY score DESC
    LIMIT 10
    """
    
    results = neo4j_client.execute_read_query(query, {"query": "związki partnerskie"})
    
    print(f"\n✓ Search without filter returned {len(results)} results")
    
    found_1457 = False
    for i, r in enumerate(results, 1):
        in_process = r['number'] in (r['processPrint'] or [])
        filter_status = "✓ PASSES" if in_process else "✗ FILTERED OUT"
        
        print(f"\n{i}. Print {r['number']} (score: {r['score']:.4f}) {filter_status}")
        print(f"   Title: {r['title'][:80]}")
        print(f"   ProcessPrint: {r['processPrint']}")
        
        if r['number'] == '1457':
            found_1457 = True
            print("   >>> THIS IS PRINT 1457! <<<")
    
    if found_1457:
        print("\n✓ Print 1457 FOUND when filter is removed!")
    else:
        print("\n✗ Print 1457 NOT FOUND even without filter")
    
    return results


def test_actual_search_function():
    """Test the actual search_prints_by_query function"""
    print("\n" + "="*60)
    print("TEST 5: Actual search_prints_by_query function")
    print("="*60)
    
    results = query_service.search_prints_by_query("związki partnerskie", limit=10)
    
    print(f"\n✓ search_prints_by_query returned {len(results)} results")
    
    found_1457 = False
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Print {r.number}")
        print(f"   Title: {r.title[:80]}")
        
        if r.number == '1457':
            found_1457 = True
            print("   >>> THIS IS PRINT 1457! <<<")
    
    if not found_1457:
        print("\n✗ Print 1457 NOT in search_prints_by_query results")
    
    return results


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("INVESTIGATING SEARCH FOR 'związki partnerskie'")
    print("="*60)
    
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j\n")
        
        # Run all tests
        print_data = check_print_1457()
        
        if print_data:
            test_fulltext_search()
            test_vector_search()
            test_search_without_filter()
            test_actual_search_function()
        
        print("\n" + "="*60)
        print("INVESTIGATION COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    main()
