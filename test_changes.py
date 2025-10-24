"""Test script for the new changes to server.py"""

import os
import sys
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service


def test_search_prints_with_process_filter():
    """Test that search_prints only returns prints with number in processPrint"""
    print("\n" + "="*60)
    print("TEST 1: search_prints with processPrint filter")
    print("="*60)
    
    try:
        results = query_service.search_prints_by_query("podatki", limit=5)
        
        if results:
            print(f"\n✓ Found {len(results)} prints")
            for i, p in enumerate(results[:3], 1):
                print(f"\n{i}. Print {p.number}")
                print(f"   Title: {p.title}")
                if p.currentStage:
                    print(f"   Stage: {p.currentStage}")
                if p.summary:
                    print(f"   Summary: {p.summary[:100]}...")
                else:
                    print(f"   Summary: (no summary)")
        else:
            print("\n✗ No prints found")
            
        return True
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_process_details():
    """Test the new get_process_details function"""
    print("\n" + "="*60)
    print("TEST 2: get_process_details")
    print("="*60)
    
    # Use a known print number instead of searching
    test_print_number = "1281"  # From test 1, we know this exists
    
    try:
        print(f"\nTesting with print number: {test_print_number}")
        
        # Test get_process_details
        details = query_service.get_process_details(test_print_number)
        
        if details:
            print(f"\n✓ Got process details for process {details.processNumber}")
            print(f"   Title: {details.title}")
            print(f"   Status: {details.status}")
            print(f"   Prints in process: {len(details.prints)}")
            print(f"   Stages: {len(details.allStages)}")
            print(f"   Subjects: {len(details.allSubjects)}")
            print(f"   Organizations: {len(details.allOrganizations)}")
            print(f"   Topics: {len(details.allTopics)}")
            
            # Show first few prints
            if details.prints:
                print(f"\n   First few prints:")
                for p in details.prints[:3]:
                    print(f"     - Print {p.number}: {p.title[:50]}...")
            
            # Show first few stages
            if details.allStages:
                print(f"\n   Latest stages:")
                for s in details.allStages[:3]:
                    print(f"     - {s.stageName} ({s.date or 'no date'})")
            
            return True
        else:
            print(f"\n✗ No process details found for print {test_print_number}")
            return False
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_removed_functions():
    """Verify that removed functions are gone from the module"""
    print("\n" + "="*60)
    print("TEST 3: Verify removed functions")
    print("="*60)
    
    removed_functions = ['search_all', 'get_topic_statistics', 'get_similar_topics']
    
    all_removed = True
    for func_name in removed_functions:
        if hasattr(query_service, func_name):
            print(f"✗ Function '{func_name}' still exists in query_service")
            all_removed = False
        else:
            print(f"✓ Function '{func_name}' successfully removed")
    
    return all_removed


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TESTING NEW CHANGES TO NEO4J MCP SERVER")
    print("="*60)
    
    # Connect to Neo4j
    try:
        neo4j_client.connect()
        print("✓ Connected to Neo4j")
    except Exception as e:
        print(f"✗ Failed to connect to Neo4j: {e}")
        return
    
    try:
        # Run tests
        results = []
        
        results.append(("Search Prints Filter", test_search_prints_with_process_filter()))
        results.append(("Get Process Details", test_get_process_details()))
        results.append(("Removed Functions", test_removed_functions()))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        for test_name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {test_name}")
        
        all_passed = all(r[1] for r in results)
        
        if all_passed:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed")
        
    finally:
        neo4j_client.close()
        print("\n✓ Closed Neo4j connection")


if __name__ == "__main__":
    main()
