#!/usr/bin/env python3
"""Test the new hybrid search implementation"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def test_hybrid_search():
    """Test hybrid search for 'związki partnerskie'"""
    print("\n" + "="*70)
    print("TESTING HYBRID SEARCH (Vector + Fulltext)")
    print("="*70)
    
    neo4j_client.connect()
    
    try:
        # Test 1: Hybrid search
        print("\n🔍 Query: 'związki partnerskie'")
        print("-" * 70)
        
        results = query_service.search_prints_by_query("związki partnerskie", limit=10)
        
        print(f"\n📊 Hybrid Search Results ({len(results)} prints):\n")
        
        found_1457 = False
        found_1458 = False
        
        for i, r in enumerate(results, 1):
            marker = ""
            if r.number == '1457':
                found_1457 = True
                marker = " ✅ MAIN BILL"
            elif r.number == '1458':
                found_1458 = True
                marker = " ✅ IMPLEMENTING PROVISIONS"
            
            print(f"{i:2}. Print {r.number}: {r.title[:60]}{marker}")
            if r.topics:
                print(f"     Topics: {', '.join(r.topics[:3])}")
        
        # Summary
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        if found_1457:
            print("✅ Print 1457 (main bill) FOUND")
        else:
            print("❌ Print 1457 (main bill) NOT FOUND")
        
        if found_1458:
            print("✅ Print 1458 (implementing provisions) FOUND")
        else:
            print("⚠️  Print 1458 (implementing provisions) NOT FOUND")
        
        # Test 2: Compare with individual methods
        print("\n" + "="*70)
        print("COMPARISON: Individual Search Methods")
        print("="*70)
        
        print("\n📈 Vector Search Only:")
        vector_results = query_service._search_prints_vector("związki partnerskie", limit=10)
        vector_has_1457 = any(r.number == '1457' for r in vector_results)
        print(f"   Results: {len(vector_results)}")
        print(f"   Has 1457: {'✅ YES' if vector_has_1457 else '❌ NO'}")
        
        print("\n📝 Fulltext Search Only:")
        fulltext_results = query_service._search_prints_fulltext("związki partnerskie", limit=10)
        fulltext_has_1457 = any(r.number == '1457' for r in fulltext_results)
        print(f"   Results: {len(fulltext_results)}")
        print(f"   Has 1457: {'✅ YES' if fulltext_has_1457 else '❌ NO'}")
        
        print("\n💡 CONCLUSION:")
        if found_1457:
            print("   Hybrid search successfully combines both methods!")
            if not vector_has_1457 and fulltext_has_1457:
                print("   → Fulltext search rescued the result that vector missed")
            elif vector_has_1457 and not fulltext_has_1457:
                print("   → Vector search rescued the result that fulltext missed")
            else:
                print("   → Both methods found it, RRF boosted its rank")
        else:
            print("   ⚠️  Still missing print 1457")
        
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    test_hybrid_search()
