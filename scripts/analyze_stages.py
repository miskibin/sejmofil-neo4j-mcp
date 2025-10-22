#!/usr/bin/env python3
"""
Analyze stage names to identify terminal stages dynamically
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from loguru import logger

logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")


def analyze_terminal_stages():
    """Analyze all stage names to find terminal ones"""
    
    neo4j_client.connect()
    
    try:
        # Get all unique stage names with counts
        query = """
        MATCH (stage:Stage)
        RETURN DISTINCT stage.stageName as stageName, count(*) as count
        ORDER BY count DESC
        """
        
        results = neo4j_client.execute_read_query(query)
        
        print("\n" + "="*80)
        print("ALL STAGE NAMES IN DATABASE")
        print("="*80)
        
        for r in results:
            print(f"{r['stageName']:60} {r['count']:>5} instances")
        
        # Now analyze which stages are terminal by checking if there are later stages
        terminal_query = """
        MATCH (process:Process)-[:HAS]->(stage:Stage)
        WITH process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        WITH process, COLLECT(stage) as stages
        WHERE size(stages) > 0
        
        WITH stages[-1] as lastStage
        RETURN DISTINCT lastStage.stageName as stageName, count(*) as count
        ORDER BY count DESC
        """
        
        print("\n" + "="*80)
        print("STAGES THAT ARE LAST IN PROCESSES (Potential Terminal Stages)")
        print("="*80)
        
        terminal_results = neo4j_client.execute_read_query(terminal_query)
        
        for r in terminal_results:
            print(f"{r['stageName']:60} {r['count']:>5} instances")
        
        # Analyze stage type distribution
        type_query = """
        MATCH (stage:Stage)
        WHERE stage.type IS NOT NULL
        RETURN DISTINCT stage.type as type, count(*) as count
        ORDER BY count DESC
        """
        
        print("\n" + "="*80)
        print("STAGE TYPES")
        print("="*80)
        
        type_results = neo4j_client.execute_read_query(type_query)
        
        for r in type_results:
            print(f"{r['type']:60} {r['count']:>5} instances")
            
    finally:
        neo4j_client.close()


def analyze_neighbor_nodes():
    """Analyze neighbor relationships for different node types"""
    
    neo4j_client.connect()
    
    try:
        print("\n" + "="*80)
        print("NEIGHBOR ANALYSIS FOR DIFFERENT NODE TYPES")
        print("="*80)
        
        # Test different node types
        node_types = ['Person', 'Print', 'Topic', 'Process', 'Club', 'Committee']
        
        for node_type in node_types:
            query = f"""
            MATCH (n:{node_type})
            WITH n LIMIT 1
            
            MATCH (n)-[r]-(neighbor)
            RETURN 
                type(r) as relationshipType,
                labels(neighbor)[0] as neighborType,
                count(*) as count
            ORDER BY count DESC
            """
            
            results = neo4j_client.execute_read_query(query)
            
            print(f"\n{node_type} Neighbors:")
            total = sum(r['count'] for r in results)
            print(f"  Total neighbors: {total}")
            
            for r in results:
                print(f"    -{r['relationshipType']}-> {r['neighborType']}: {r['count']}")
                
    finally:
        neo4j_client.close()


if __name__ == "__main__":
    analyze_terminal_stages()
    analyze_neighbor_nodes()
