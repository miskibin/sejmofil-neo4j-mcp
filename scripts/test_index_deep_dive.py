#!/usr/bin/env python3
"""Deep dive into fulltext index issues"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def check_fulltext_index_config():
    """Check fulltext index configuration"""
    print("\n" + "="*60)
    print("TEST 1: Fulltext Index Configuration")
    print("="*60)
    
    query = """
    SHOW INDEXES
    YIELD name, type, labelsOrTypes, properties
    WHERE type = 'FULLTEXT'
    RETURN name, type, labelsOrTypes, properties
    """
    
    results = neo4j_client.execute_read_query(query, {})
    
    for r in results:
        print(f"\nIndex: {r['name']}")
        print(f"  Type: {r['type']}")
        print(f"  Labels: {r['labelsOrTypes']}")
        print(f"  Properties: {r['properties']}")


def test_direct_title_search():
    """Test searching for print 1457 by its exact title"""
    print("\n" + "="*60)
    print("TEST 2: Search by Exact Title")
    print("="*60)
    
    query = """
    CALL db.index.fulltext.queryNodes("print_content", $query) 
    YIELD node as print, score
    
    RETURN 
      print.number as number,
      print.title as title,
      score
    ORDER BY score DESC
    LIMIT 10
    """
    
    # Try exact title
    results = neo4j_client.execute_read_query(query, {"query": "Poselski projekt ustawy o związkach partnerskich"})
    
    print(f"\nSearch for exact title returned {len(results)} results:")
    for r in results:
        marker = " <<< PRINT 1457" if r['number'] == '1457' else ""
        print(f"  {r['number']}: {r['title'][:80]} (score: {r['score']:.4f}){marker}")


def test_simple_keywords():
    """Test with simpler keyword combinations"""
    print("\n" + "="*60)
    print("TEST 3: Simple Keywords")
    print("="*60)
    
    queries = [
        "związkach",
        "partnerskich", 
        "związek partnerski",
        "1457"
    ]
    
    for test_query in queries:
        print(f"\n  Testing: '{test_query}'")
        
        query = """
        CALL db.index.fulltext.queryNodes("print_content", $query) 
        YIELD node as print, score
        WHERE print.number = '1457'
        RETURN 
          print.number as number,
          print.title as title,
          score
        LIMIT 1
        """
        
        results = neo4j_client.execute_read_query(query, {"query": test_query})
        
        if results:
            print(f"    ✓ FOUND print 1457 (score: {results[0]['score']:.4f})")
        else:
            print(f"    ✗ NOT FOUND")


def check_print_indexed():
    """Check if print 1457 is even in the fulltext index"""
    print("\n" + "="*60)
    print("TEST 4: Check if Print 1457 is Indexed")
    print("="*60)
    
    # Try to get ANY result for print 1457 from the index
    query = """
    CALL db.index.fulltext.queryNodes("print_content", "*") 
    YIELD node as print, score
    WHERE print.number = '1457'
    RETURN 
      print.number as number,
      print.title as title,
      print.summary as summary,
      score
    LIMIT 1
    """
    
    results = neo4j_client.execute_read_query(query, {})
    
    if results:
        print(f"\n✓ Print 1457 IS in the fulltext index")
        print(f"  Score: {results[0]['score']:.4f}")
    else:
        print(f"\n✗ Print 1457 is NOT in the fulltext index!")
        print("  This could mean:")
        print("  - The index doesn't include this print's properties")
        print("  - The print was added after index creation")
        print("  - The index needs to be rebuilt")


def compare_indexed_vs_all():
    """Compare prints that are indexed vs all prints"""
    print("\n" + "="*60)
    print("TEST 5: Compare Indexed vs All Prints")
    print("="*60)
    
    # Count all prints
    all_query = """
    MATCH (p:Print)
    WHERE p.number = '1457'
    RETURN count(p) as count
    """
    
    all_count = neo4j_client.execute_read_query(all_query, {})[0]['count']
    print(f"\nPrints with number='1457' in database: {all_count}")
    
    # Try to find in index with wildcard
    index_query = """
    CALL db.index.fulltext.queryNodes("print_content", "projekt~") 
    YIELD node as print
    WHERE print.number = '1457'
    RETURN count(print) as count
    """
    
    index_count = neo4j_client.execute_read_query(index_query, {})[0]['count']
    print(f"Print 1457 findable in fulltext index: {index_count}")
    
    if all_count > 0 and index_count == 0:
        print("\n⚠️  ISSUE CONFIRMED: Print exists but is not in fulltext index")


def test_vector_embedding_exists():
    """Check if print 1457 has a vector embedding"""
    print("\n" + "="*60)
    print("TEST 6: Check Vector Embedding")
    print("="*60)
    
    query = """
    MATCH (p:Print {number: '1457'})
    RETURN 
      p.number as number,
      p.embedding IS NOT NULL as hasEmbedding,
      size(p.embedding) as embeddingSize
    """
    
    results = neo4j_client.execute_read_query(query, {})
    
    if results:
        r = results[0]
        if r['hasEmbedding']:
            print(f"\n✓ Print 1457 HAS vector embedding (size: {r['embeddingSize']})")
        else:
            print(f"\n✗ Print 1457 does NOT have vector embedding")
    
    # Try vector search specifically for 1457
    from sejmofil_mcp.embeddings import embeddings_service
    
    if embeddings_service.is_available():
        embedding = embeddings_service.generate_embedding("związki partnerskie")
        
        vector_query = """
        CALL db.index.vector.queryNodes('printEmbeddingIndex', 100, $embedding)
        YIELD node as print, score
        WHERE print.number = '1457'
        RETURN 
          print.number as number,
          score
        LIMIT 1
        """
        
        vector_results = neo4j_client.execute_read_query(vector_query, {"embedding": embedding})
        
        if vector_results:
            print(f"✓ Print 1457 found in vector search (score: {vector_results[0]['score']:.4f})")
        else:
            print(f"✗ Print 1457 NOT found in vector search (searched top 100)")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DEEP DIVE: FULLTEXT INDEX INVESTIGATION")
    print("="*60)
    
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j\n")
        
        check_fulltext_index_config()
        test_direct_title_search()
        test_simple_keywords()
        check_print_indexed()
        compare_indexed_vs_all()
        test_vector_embedding_exists()
        
        print("\n" + "="*60)
        print("DEEP DIVE COMPLETE")
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
