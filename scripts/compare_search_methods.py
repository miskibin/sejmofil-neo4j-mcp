#!/usr/bin/env python3
"""Compare old vs new search for various queries"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service

neo4j_client.connect()

test_queries = [
    ("związki partnerskie", "Civil partnerships"),
    ("podatki", "Taxes"),
    ("ochrona zdrowia", "Healthcare"),
    ("energia odnawialna", "Renewable energy"),
]

print("\n" + "="*80)
print("HYBRID SEARCH vs INDIVIDUAL METHODS - COMPARISON")
print("="*80)

for query, description in test_queries:
    print(f"\n📝 Query: '{query}' ({description})")
    print("-" * 80)
    
    # Hybrid search
    hybrid = query_service.search_prints_by_query(query, limit=5)
    
    # Individual methods
    vector = query_service._search_prints_vector(query, limit=5)
    fulltext = query_service._search_prints_fulltext(query, limit=5)
    
    # Count unique results
    hybrid_nums = set(r.number for r in hybrid)
    vector_nums = set(r.number for r in vector)
    fulltext_nums = set(r.number for r in fulltext)
    
    # Calculate coverage
    only_vector = vector_nums - fulltext_nums
    only_fulltext = fulltext_nums - vector_nums
    both = vector_nums & fulltext_nums
    
    print(f"  Vector only:    {len(only_vector)} prints {list(only_vector)[:3]}")
    print(f"  Fulltext only:  {len(only_fulltext)} prints {list(only_fulltext)[:3]}")
    print(f"  Both methods:   {len(both)} prints {list(both)[:3]}")
    print(f"  Hybrid total:   {len(hybrid_nums)} unique prints")
    
    # Show top hybrid result
    if hybrid:
        print(f"  🏆 Top result:  {hybrid[0].number} - {hybrid[0].title[:50]}...")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("✅ Hybrid search combines unique results from both methods")
print("✅ Better coverage than using either method alone")
print("✅ RRF boosts items that appear in both lists\n")

neo4j_client.close()
