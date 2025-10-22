#!/usr/bin/env python3
"""
Test MCP with realistic Polish user queries
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")


def test_query(description, query_func, success_check=None):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    
    try:
        result = query_func()
        print(f"\n✅ Query executed successfully")
        
        if success_check:
            if success_check(result):
                print(f"✅ Result validation passed")
            else:
                print(f"⚠️  Result validation failed or empty results")
        
        # Show sample of results
        if isinstance(result, list):
            print(f"\nFound {len(result)} results")
            for i, item in enumerate(result[:3], 1):
                if hasattr(item, 'title'):
                    print(f"  {i}. {item.title[:80]}")
                elif hasattr(item, 'name'):
                    print(f"  {i}. {item.name}")
                else:
                    print(f"  {i}. {item}")
        elif isinstance(result, dict):
            print(f"\nResult keys: {list(result.keys())}")
            for key, value in list(result.items())[:3]:
                print(f"  {key}: {value}")
        else:
            print(f"\nResult: {str(result)[:200]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


def main():
    """Run realistic query tests"""
    
    neo4j_client.connect()
    
    try:
        print("\n" + "="*80)
        print("TESTING MCP WITH REALISTIC USER QUERIES")
        print("="*80)
        
        # Test 1: Search for abortion-related prints
        test_query(
            "Ostatni proces na temat aborcji (Recent process about abortion)",
            lambda: query_service.search_prints_by_query("aborcja", limit=5, status_filter='all'),
            lambda r: len(r) > 0
        )
        
        # Test 2: Search active legislation about taxes
        test_query(
            "Aktywne procesy o podatkach (Active processes about taxes)",
            lambda: query_service.search_prints_by_query("podatki", limit=5, status_filter='active'),
            lambda r: len(r) > 0
        )
        
        # Test 3: Search for healthcare legislation
        test_query(
            "Ustawy o ochronie zdrowia (Healthcare laws)",
            lambda: query_service.search_prints_by_query("ochrona zdrowia", limit=5, status_filter='all'),
            lambda r: len(r) > 0
        )
        
        # Test 4: Search for defense/military legislation
        test_query(
            "Projekty ustaw o obronie narodowej (National defense bills)",
            lambda: query_service.search_prints_by_query("obrona narodowa", limit=5, status_filter='all'),
            lambda r: len(r) > 0
        )
        
        # Test 5: Find MP by name
        test_query(
            "Znajdź posła o nazwisku Tusk (Find MP named Tusk)",
            lambda: query_service.find_person_by_name("Tusk"),
            lambda r: len(r) > 0
        )
        
        # Test 6: Get club statistics for PiS
        test_query(
            "Statystyki klubu PiS (PiS club statistics)",
            lambda: query_service.get_club_statistics("Klub Parlamentarny Prawo i Sprawiedliwość"),
            lambda r: r is not None and r.memberCount > 0
        )
        
        # Test 7: List all clubs
        test_query(
            "Lista wszystkich klubów parlamentarnych (List all parliamentary clubs)",
            lambda: query_service.list_clubs(),
            lambda r: len(r) > 0
        )
        
        # Test 8: Get topic statistics
        test_query(
            "Statystyki tematu 'Podatki' (Tax topic statistics)",
            lambda: query_service.get_topic_statistics("Podatki"),
            lambda r: r and 'totalPrints' in r
        )
        
        # Test 9: Search for environment-related legislation
        test_query(
            "Projekty o środowisku i klimacie (Environment and climate bills)",
            lambda: query_service.search_prints_by_query("środowisko klimat energia odnawialna", limit=5),
            lambda r: len(r) > 0
        )
        
        # Test 10: Find finished legislation
        test_query(
            "Zakończone procesy legislacyjne (Finished legislative processes)",
            lambda: query_service.search_prints_by_query("ustawa", limit=5, status_filter='finished'),
            lambda r: len(r) > 0
        )
        
        # Test 11: Explore a Print node
        print(f"\n{'='*80}")
        print("TEST: Eksploracja druku (Explore a print)")
        print(f"{'='*80}")
        
        # Get a sample print first
        prints = query_service.search_prints_by_query("podatki", limit=1)
        if prints:
            print_num = prints[0].number
            print(f"\n✅ Found print: {print_num}")
            
            neighbors = query_service.get_node_neighbors('Print', print_num, limit=5)
            if neighbors:
                print(f"✅ Found {len(neighbors)} relationship types:")
                for rel_type, data in list(neighbors.items())[:3]:
                    print(f"  - {rel_type}: {data['totalCount']} {data['neighborType']} nodes")
            else:
                print("⚠️  No neighbors found")
        else:
            print("❌ Could not find sample print")
        
        # Test 12: Check if a process is active
        print(f"\n{'='*80}")
        print("TEST: Sprawdź status procesu (Check process status)")
        print(f"{'='*80}")
        
        # Get a sample process
        query = "MATCH (p:Process) RETURN p.number as number LIMIT 1"
        process_results = neo4j_client.execute_read_query(query)
        if process_results:
            process_num = process_results[0]['number']
            print(f"\n✅ Testing with process: {process_num}")
            
            status = query_service.get_process_status(process_num)
            if status:
                print(f"✅ Process status: {status.status}")
                print(f"   Current stage: {status.currentStage}")
                print(f"   Total stages: {len(status.allStages) if status.allStages else 0}")
            else:
                print("⚠️  Could not get process status")
        else:
            print("❌ Could not find sample process")
        
        print("\n" + "="*80)
        print("✅ ALL REALISTIC QUERY TESTS COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
