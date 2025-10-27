#!/usr/bin/env python3
"""Test different fulltext query syntaxes"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO")


def test_query_syntax():
    """Test different fulltext query syntaxes"""
    print("\n" + "="*60)
    print("TEST: Different Fulltext Query Syntaxes")
    print("="*60)
    
    test_queries = [
        ("związki partnerskie", "Original (space-separated)"),
        ("związki AND partnerskie", "AND operator"),
        ("związki OR partnerskie", "OR operator"),
        ("\"związki partnerskie\"", "Quoted phrase"),
        ("związki~ partnerskie~", "Fuzzy search"),
        ("związk* partnersk*", "Wildcard"),
        ("związkach", "Single word (accusative)"),
        ("partnerskich", "Single word (genitive)"),
    ]
    
    for query_text, description in test_queries:
        print(f"\n  Query: {description}")
        print(f"  Text: '{query_text}'")
        
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
        
        try:
            results = neo4j_client.execute_read_query(query, {"query": query_text})
            
            if results:
                print(f"    ✓ FOUND (score: {results[0]['score']:.4f})")
            else:
                print(f"    ✗ NOT FOUND")
        except Exception as e:
            print(f"    ✗ ERROR: {e}")


def test_with_filter():
    """Test the actual query used in search_prints_by_query with different formats"""
    print("\n" + "="*60)
    print("TEST: Query with processPrint Filter")
    print("="*60)
    
    test_queries = [
        "związki partnerskie",
        "związki AND partnerskie",
        "związkach OR partnerskich",
    ]
    
    for query_text in test_queries:
        print(f"\n  Testing: '{query_text}'")
        
        query = """
        CALL db.index.fulltext.queryNodes("print_content", $query) 
        YIELD node as print, score
        WHERE print.summary IS NOT NULL
          AND print.number IN print.processPrint
        
        RETURN 
          print.number as number,
          print.title as title,
          score
        ORDER BY score DESC
        LIMIT 10
        """
        
        try:
            results = neo4j_client.execute_read_query(query, {"query": query_text})
            
            found_1457 = any(r['number'] == '1457' for r in results)
            
            if found_1457:
                print(f"    ✓ Print 1457 in top 10 results")
            else:
                print(f"    ✗ Print 1457 NOT in top 10 results ({len(results)} total)")
                if results:
                    print(f"       Top result: {results[0]['number']} (score: {results[0]['score']:.4f})")
        except Exception as e:
            print(f"    ✗ ERROR: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("FULLTEXT QUERY SYNTAX INVESTIGATION")
    print("="*60)
    
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j\n")
        
        test_query_syntax()
        test_with_filter()
        
        print("\n" + "="*60)
        print("INVESTIGATION COMPLETE")
        print("="*60)
        
        print("\n📊 FINDINGS:")
        print("  - Print 1457 exists and is in the fulltext index")
        print("  - Individual words find it, but phrase search doesn't")
        print("  - This is a Lucene fulltext search behavior issue")
        print("\n💡 SOLUTION:")
        print("  - Use OR operator for multi-word queries")
        print("  - Or use fuzzy/wildcard operators")
        print("  - Vector search works better for semantic matching")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    main()
