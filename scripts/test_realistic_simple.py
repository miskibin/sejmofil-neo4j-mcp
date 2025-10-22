#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MCP with realistic Polish user queries (simplified)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service


def main():
    """Run realistic query tests"""
    
    neo4j_client.connect()
    
    try:
        print("\n" + "="*80)
        print("TESTING MCP WITH REALISTIC USER QUERIES")
        print("="*80)
        
        # Test 1: Abortion-related prints
        print("\n[1] Query: Ostatni proces na temat aborcji")
        results = query_service.search_prints_by_query("aborcja", limit=3, status_filter='all')
        print(f"    Results: {len(results)} prints found")
        for r in results[:2]:
            print(f"      - Print {r.number}")
        
        # Test 2: Active tax legislation
        print("\n[2] Query: Aktywne procesy o podatkach")
        results = query_service.search_prints_by_query("podatki", limit=3, status_filter='active')
        print(f"    Results: {len(results)} active prints found")
        
        # Test 3: Healthcare legislation
        print("\n[3] Query: Ustawy o ochronie zdrowia")
        results = query_service.search_prints_by_query("ochrona zdrowia", limit=3)
        print(f"    Results: {len(results)} prints found")
        
        # Test 4: Find MP
        print("\n[4] Query: Znajdz posla Tusk")
        results = query_service.find_person_by_name("Tusk")
        print(f"    Results: {len(results)} MPs found")
        if results:
            print(f"      - {results[0].name} ({results[0].club})")
        
        # Test 5: Club statistics
        print("\n[5] Query: Statystyki klubu PiS")
        result = query_service.get_club_statistics("Klub Parlamentarny Prawo i Sprawiedliwość")
        if result:
            print(f"    Results: {result.memberCount} members, {result.authoredPrints} authored prints")
        else:
            print("    Results: Club not found")
        
        # Test 6: List clubs
        print("\n[6] Query: Lista klubow parlamentarnych")
        results = query_service.list_clubs()
        print(f"    Results: {len(results)} clubs found")
        for club in results[:3]:
            print(f"      - {club.name}: {club.memberCount} members")
        
        # Test 7: Topic statistics
        print("\n[7] Query: Statystyki tematu Podatki")
        result = query_service.get_topic_statistics("Podatki")
        if result and 'totalPrints' in result:
            print(f"    Results: {result['totalPrints']} total prints, {result.get('activePrints', 0)} active")
        else:
            print("    Results: Topic not found or no data")
        
        # Test 8: Explore a print
        print("\n[8] Query: Eksploracja druku (neighbors)")
        prints = query_service.search_prints_by_query("podatki", limit=1)
        if prints:
            print_num = prints[0].number
            neighbors = query_service.get_node_neighbors('Print', print_num, limit=5)
            print(f"    Results: Print {print_num} has {len(neighbors)} relationship types")
            for rel_type, data in list(neighbors.items())[:3]:
                print(f"      - {rel_type}: {data['totalCount']} neighbors")
        else:
            print("    Results: No print found")
        
        # Test 9: Process status
        print("\n[9] Query: Sprawdz status procesu")
        query = "MATCH (p:Process) RETURN p.number as number LIMIT 1"
        process_results = neo4j_client.execute_read_query(query)
        if process_results:
            process_num = process_results[0]['number']
            status = query_service.get_process_status(process_num)
            if status:
                print(f"    Results: Process {process_num} is {status.status}")
                print(f"             Stage: {status.currentStage}")
            else:
                print("    Results: Process not found")
        
        # Test 10: Environment and climate
        print("\n[10] Query: Projekty o srodowisku i klimacie")
        results = query_service.search_prints_by_query("środowisko klimat", limit=3)
        print(f"     Results: {len(results)} prints found")
        
        # Test 11: Finished processes
        print("\n[11] Query: Zakonczoneпроцессы legislacyjne")
        results = query_service.search_prints_by_query("ustawa", limit=3, status_filter='finished')
        print(f"     Results: {len(results)} finished prints found")
        
        # Test 12: MP activity
        print("\n[12] Query: Aktywnosc posla")
        mps = query_service.find_person_by_name("Tusk")
        if mps and mps[0].id:
            activity = query_service.get_person_activity(mps[0].id)
            if activity:
                print(f"     Results: {activity.person.name}")
                print(f"              Speeches: {activity.speechCount}")
                print(f"              Authored prints: {len(activity.authoredPrints)}")
                print(f"              Committees: {len(activity.committees)}")
            else:
                print("     Results: No activity data")
        else:
            print("     Results: MP not found")
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    main()
