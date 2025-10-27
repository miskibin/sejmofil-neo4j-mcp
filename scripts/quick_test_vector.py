#!/usr/bin/env python3
"""Quick test of improved vector search"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service

neo4j_client.connect()

print("Testing improved vector search for 'związki partnerskie':\n")

results = query_service.search_prints_by_query('związki partnerskie', limit=10)

print(f"Found {len(results)} results:\n")

found_1457 = False
for i, r in enumerate(results, 1):
    marker = ' <<< FOUND 1457!' if r.number == '1457' else ''
    print(f"{i}. {r.number}: {r.title[:70]}{marker}")
    if r.number == '1457':
        found_1457 = True

print()
if found_1457:
    print("✅ SUCCESS: Print 1457 now found in vector search!")
else:
    print("⚠️  Print 1457 still not in top 10 vector results")
    print("   (This is okay - fulltext search will catch it)")

neo4j_client.close()
