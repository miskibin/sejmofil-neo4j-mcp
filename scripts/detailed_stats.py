#!/usr/bin/env python3
"""
Detailed database statistics and sample queries for Sejmofil Neo4j database
"""

import sys
import os
from pathlib import Path

# Add the sejmofil_mcp package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.config import settings


def connect_to_database():
    """Connect to the Neo4j database"""
    try:
        neo4j_client.connect()
        print("✅ Successfully connected to Neo4j database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        return False


def get_detailed_statistics():
    """Get detailed statistics about the database"""
    print("\n📊 DETAILED DATABASE STATISTICS")
    print("=" * 60)

    # Get total counts
    print("\n🔢 TOTAL COUNTS:")
    total_nodes_query = "MATCH (n) RETURN count(n) as total_nodes"
    total_rels_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"

    try:
        nodes_result = neo4j_client.execute_read_query(total_nodes_query)
        rels_result = neo4j_client.execute_read_query(total_rels_query)

        total_nodes = nodes_result[0]['total_nodes']
        total_rels = rels_result[0]['total_relationships']

        print(f"  Total Nodes: {total_nodes:,}")
        print(f"  Total Relationships: {total_rels:,}")
        print(".2f")
    except Exception as e:
        print(f"Error getting totals: {e}")

    # Get detailed node counts
    print("\n🏷️  NODES BY LABEL (sorted by count):")
    node_counts_query = """
    CALL db.labels() YIELD label
    CALL {
        WITH label
        MATCH (n)
        WHERE label IN labels(n)
        RETURN count(n) as count
    }
    RETURN label, count
    ORDER BY count DESC
    """

    try:
        results = neo4j_client.execute_read_query(node_counts_query)
        for result in results:
            label = result['label']
            count = result['count']
            percentage = (count / total_nodes) * 100 if total_nodes > 0 else 0
            print("6")
    except Exception as e:
        print(f"Error getting node counts: {e}")

    # Get detailed relationship counts
    print("\n🔗 RELATIONSHIPS BY TYPE (sorted by count):")
    rel_counts_query = """
    CALL db.relationshipTypes() YIELD relationshipType
    CALL {
        WITH relationshipType
        MATCH ()-[r]-()
        WHERE type(r) = relationshipType
        RETURN count(r) as count
    }
    RETURN relationshipType, count
    ORDER BY count DESC
    """

    try:
        results = neo4j_client.execute_read_query(rel_counts_query)
        for result in results:
            rel_type = result['relationshipType']
            count = result['count']
            percentage = (count / total_rels) * 100 if total_rels > 0 else 0
            print("6")
    except Exception as e:
        print(f"Error getting relationship counts: {e}")


def get_parliamentary_statistics():
    """Get statistics specific to parliamentary data"""
    print("\n🏛️  PARLIAMENTARY STATISTICS")
    print("=" * 60)

    # MPs statistics
    print("\n👥 MEMBERS OF PARLIAMENT:")
    mp_stats_query = """
    MATCH (p:Person)
    WHERE p.club IS NOT NULL
    RETURN
        count(p) as total_mps,
        sum(CASE WHEN p.active = true THEN 1 ELSE 0 END) as active_mps,
        count(DISTINCT p.club) as total_clubs
    """

    try:
        results = neo4j_client.execute_read_query(mp_stats_query)
        if results:
            stats = results[0]
            print(f"  Total MPs: {stats['total_mps']}")
            print(f"  Active MPs: {stats['active_mps']}")
            print(f"  Parliamentary Clubs: {stats['total_clubs']}")
    except Exception as e:
        print(f"Error getting MP stats: {e}")

    # Club statistics
    print("\n🎯 CLUB STATISTICS:")
    club_stats_query = """
    MATCH (p:Person)
    WHERE p.club IS NOT NULL
    WITH p.club as club, count(p) as members,
         sum(CASE WHEN p.active = true THEN 1 ELSE 0 END) as active_members
    RETURN club, members, active_members
    ORDER BY members DESC
    """

    try:
        results = neo4j_client.execute_read_query(club_stats_query)
        for result in results:
            club = result['club']
            members = result['members']
            active = result['active_members']
            print(f"  {club}: {members} members ({active} active)")
    except Exception as e:
        print(f"Error getting club stats: {e}")

    # Legislative activity
    print("\n📄 LEGISLATIVE ACTIVITY:")
    activity_stats_query = """
    MATCH (print:Print)
    OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
    OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)

    WITH print, process, stage
    ORDER BY stage.date DESC, stage.number DESC

    WITH print, process, COLLECT(stage)[0] as latestStage

    WITH
        count(DISTINCT print) as total_prints,
        sum(CASE
            WHEN process IS NULL
                 OR latestStage IS NULL
                 OR (latestStage.stageName IS NOT NULL
                     AND NOT latestStage.stageName IN [
                       'Publikacja w Dzienniku Ustaw',
                       'Odrzucenie projektu ustawy',
                       'Wycofanie projektu'
                     ])
            THEN 1
            ELSE 0
        END) as active_prints,
        sum(CASE
            WHEN latestStage.stageName IN [
              'Publikacja w Dzienniku Ustaw',
              'Odrzucenie projektu ustawy',
              'Wycofanie projektu'
            ]
            THEN 1
            ELSE 0
        END) as finished_prints
    RETURN total_prints, active_prints, finished_prints
    """

    try:
        results = neo4j_client.execute_read_query(activity_stats_query)
        if results:
            stats = results[0]
            print(f"  Total Legislative Prints: {stats['total_prints']}")
            print(f"  Active Prints: {stats['active_prints']}")
            print(f"  Finished Prints: {stats['finished_prints']}")
    except Exception as e:
        print(f"Error getting activity stats: {e}")

    # Speech statistics
    print("\n🎤 SPEECH STATISTICS:")
    speech_stats_query = """
    MATCH (person:Person)-[:SAID]->(statement:Statement)
    RETURN count(DISTINCT statement) as total_speeches,
           count(DISTINCT person) as speakers
    """

    try:
        results = neo4j_client.execute_read_query(speech_stats_query)
        if results:
            stats = results[0]
            print(f"  Total Speeches: {stats['total_speeches']:,}")
            print(f"  Speakers: {stats['speakers']}")
            if stats['speakers'] > 0:
                avg_speeches = stats['total_speeches'] / stats['speakers']
                print(".1f")
    except Exception as e:
        print(f"Error getting speech stats: {e}")


def sample_recent_activity():
    """Sample recent parliamentary activity"""
    print("\n🕐 RECENT ACTIVITY SAMPLES")
    print("=" * 60)

    # Recent prints
    print("\n📄 RECENT LEGISLATIVE PRINTS:")
    recent_prints_query = """
    MATCH (print:Print)
    WHERE print.documentDate IS NOT NULL
    RETURN print.number as number,
           print.title as title,
           print.documentDate as date
    ORDER BY print.documentDate DESC
    LIMIT 5
    """

    try:
        results = neo4j_client.execute_read_query(recent_prints_query)
        for result in results:
            print(f"  {result['number']}: {result['title'][:80]}... ({result['date']})")
    except Exception as e:
        print(f"Error getting recent prints: {e}")

    # Recent speeches
    print("\n🎤 RECENT SPEECHES:")
    recent_speeches_query = """
    MATCH (person:Person)-[r:SAID]->(statement:Statement)
    WHERE r.date IS NOT NULL
    RETURN person.firstLastName as speaker,
           statement.statement_official_topic as topic,
           r.date as date
    ORDER BY r.date DESC
    LIMIT 5
    """

    try:
        results = neo4j_client.execute_read_query(recent_speeches_query)
        for result in results:
            speaker = result['speaker']
            topic = result['topic'][:60] + "..." if result['topic'] and len(result['topic']) > 60 else result['topic']
            date = result['date']
            print(f"  {speaker}: {topic} ({date})")
    except Exception as e:
        print(f"Error getting recent speeches: {e}")


def main():
    """Main function"""
    print("📈 SEJMOFIL DATABASE DETAILED STATISTICS")
    print("=" * 60)
    print(f"Host: {settings.NEO4J_HOST}")
    print(f"User: {settings.NEO4J_USER}")

    if not connect_to_database():
        return

    try:
        get_detailed_statistics()
        get_parliamentary_statistics()
        sample_recent_activity()

    finally:
        neo4j_client.close()
        print("\n✅ Database connection closed")


if __name__ == "__main__":
    main()