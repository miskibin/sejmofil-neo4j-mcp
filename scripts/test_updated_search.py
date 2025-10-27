#!/usr/bin/env python3
"""Test the updated search_prints function"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from sejmofil_mcp.embeddings import embeddings_service
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def test_search_without_embeddings():
    """Test fulltext search without embeddings (force fallback)"""
    print("\n" + "="*60)
    print("TEST 1: Fulltext Search (no embeddings)")
    print("="*60)
    
    # Temporarily disable embeddings to force fulltext search
    original_key = embeddings_service.client.api_key if hasattr(embeddings_service, 'client') else None
    
    try:
        # Force unavailable
        if hasattr(embeddings_service, 'client'):
            embeddings_service.client.api_key = None
        
        results = query_service._search_prints_fulltext("związki partnerskie", limit=10)
        
        print(f"\n✓ Fulltext search returned {len(results)} results")
        
        found_1457 = False
        for i, r in enumerate(results, 1):
            marker = " <<< FOUND IT!" if r.number == '1457' else ""
            print(f"{i}. Print {r.number}: {r.title[:70]}{marker}")
            if r.number == '1457':
                found_1457 = True
        
        if found_1457:
            print("\n✅ SUCCESS: Print 1457 found with new fulltext search!")
        else:
            print("\n❌ FAILED: Print 1457 still not found")
        
        return found_1457
        
    finally:
        # Restore original state
        if original_key and hasattr(embeddings_service, 'client'):
            embeddings_service.client.api_key = original_key


def test_search_with_embeddings():
    """Test with vector embeddings enabled"""
    print("\n" + "="*60)
    print("TEST 2: Vector Search (with embeddings)")
    print("="*60)
    
    if not embeddings_service.is_available():
        print("⚠️  Embeddings not available, skipping vector search test")
        return None
    
    results = query_service.search_prints_by_query("związki partnerskie", limit=10)
    
    print(f"\n✓ Vector search returned {len(results)} results")
    
    found_1457 = False
    for i, r in enumerate(results, 1):
        marker = " <<< FOUND IT!" if r.number == '1457' else ""
        print(f"{i}. Print {r.number}: {r.title[:70]}{marker}")
        if r.number == '1457':
            found_1457 = True
    
    if found_1457:
        print("\n✅ SUCCESS: Print 1457 found with vector search!")
    else:
        print("\n⚠️  Print 1457 not in top 10 vector results (might have lower similarity)")
    
    return found_1457


def test_various_queries():
    """Test with various related queries"""
    print("\n" + "="*60)
    print("TEST 3: Various Related Queries")
    print("="*60)
    
    test_queries = [
        "związki partnerskie",
        "partnerstwa",
        "partnerstwo",
        "LGBT",
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = query_service.search_prints_by_query(query, limit=5)
        
        found_1457 = any(r.number == '1457' for r in results)
        status = "✓ FOUND 1457" if found_1457 else f"✗ not found ({len(results)} results)"
        print(f"    {status}")
        
        if results and not found_1457:
            print(f"    Top result: {results[0].number} - {results[0].title[:60]}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TESTING UPDATED SEARCH FUNCTION")
    print("="*60)
    
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j\n")
        
        fulltext_result = test_search_without_embeddings()
        vector_result = test_search_with_embeddings()
        test_various_queries()
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if fulltext_result:
            print("✅ Fulltext search: FIXED - now finds print 1457")
        else:
            print("❌ Fulltext search: Still has issues")
        
        if vector_result is not None:
            if vector_result:
                print("✅ Vector search: Works correctly")
            else:
                print("⚠️  Vector search: Print 1457 not in top 10 (semantic relevance)")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    main()
