"""
Script to test all MCP tools and generate results.txt
"""

from sejmofil_mcp.queries import query_service
from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.models import PrintShort
from datetime import datetime


def format_print(print_obj: PrintShort, index: int = None) -> list:
    """
    Format a single print object for consistent output.
    Returns a list of strings to append to results.
    """
    lines = []
    
    # Add index if provided
    if index is not None:
        lines.append(f"{index}. Print {print_obj.number}")
    else:
        lines.append(f"Print {print_obj.number}")
    
    # Title
    lines.append(f"   {print_obj.title}")
    
    # Document date (without timestamp)
    if print_obj.documentDate:
        date_only = print_obj.documentDate.split('T')[0] if 'T' in print_obj.documentDate else print_obj.documentDate
        lines.append(f"   Date: {date_only}")
    
    # Current stage with stage date (without timestamp)
    if print_obj.currentStage:
        stage_info = f"   Stage: {print_obj.currentStage}"
        if print_obj.stageDate:
            stage_date_only = print_obj.stageDate.split('T')[0] if 'T' in print_obj.stageDate else print_obj.stageDate
            stage_info += f" ({stage_date_only})"
        lines.append(stage_info)
    
    # Summary
    if print_obj.summary:
        lines.append(f"   {print_obj.summary}")
    
    lines.append("")  # Empty line after each print
    return lines


def save_results():
    """Call all MCP functions and save results"""
    
    results = []
    results.append("=" * 80)
    results.append("MCP TOOLS RESULTS - Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    results.append("=" * 80)
    results.append("")
    
    # Connect to database
    neo4j_client.connect()
    
    try:
        # 1. search_prints - use fulltext directly
        results.append("\n" + "=" * 80)
        results.append("1. search_prints(query='podatki', limit=3, status='all')")
        results.append("=" * 80)
        prints = query_service._search_prints_fulltext("podatki", limit=3)
        if prints:
            results.append(f"\nFound {len(prints)} prints:\n")
            for i, p in enumerate(prints, 1):
                results.extend(format_print(p, index=i))
        
        # 2. search_prints with status filter
        results.append("\n" + "=" * 80)
        results.append("2. search_prints(query='obrona', limit=3, status='active')")
        results.append("=" * 80)
        prints = query_service._search_prints_fulltext("obrona", limit=3, status_filter='active')
        if prints:
            results.append(f"\nFound {len(prints)} active prints:\n")
            for i, p in enumerate(prints, 1):
                results.extend(format_print(p, index=i))
        
        # 3. get_process_details
        results.append("\n" + "=" * 80)
        results.append("3. get_process_details(print_number='1441')")
        results.append("=" * 80)
        details = query_service.get_process_details("1441")
        if details:
            results.append(f"\nProcess {details.processNumber}")
            results.append(f"Title: {details.title}")
            results.append(f"Status: {details.status}")
            if details.currentStage:
                results.append(f"Current Stage: {details.currentStage}")
            
            # Show all prints with same format as search results
            if details.prints:
                results.append(f"\nPrints in this process ({len(details.prints)}):\n")
                for i, p in enumerate(details.prints, 1):
                    results.extend(format_print(p, index=i))
            
            # Show all stages with dates
            if details.allStages:
                results.append(f"\nAll Stages ({len(details.allStages)}):")
                for s in details.allStages:
                    stage_date = s.date if s.date else ''
                    if stage_date and 'T' in stage_date:
                        stage_date = stage_date.split('T')[0]
                    results.append(f"  - {s.stageName} ({stage_date})")

        
        # 4. get_process_status
        results.append("\n" + "=" * 80)
        results.append("4. get_process_status(process_number='X0-P-1441')")
        results.append("=" * 80)
        status = query_service.get_process_status("X0-P-1441")
        if status:
            results.append(f"\nProcess {status.processNumber}")
            results.append(f"Status: {status.status}")
            if status.currentStage:
                results.append(f"Current Stage: {status.currentStage}")
            if status.allStages:
                results.append(f"\nStages ({len(status.allStages)}):")
                for s in status.allStages[:5]:
                    results.append(f"  - {s.stageName}")
        
        # 5. find_mp_by_name
        results.append("\n" + "=" * 80)
        results.append("5. find_mp_by_name(name='Tusk')")
        results.append("=" * 80)
        mps = query_service.find_person_by_name("Tusk")
        if mps:
            results.append(f"\nFound {len(mps)} MPs:\n")
            for i, mp in enumerate(mps[:5], 1):
                results.append(f"{i}. {mp.name} ({mp.club}) - ID: {mp.id}")
        
        # 6. get_mp_activity
        results.append("\n" + "=" * 80)
        results.append("6. get_mp_activity(person_id=400)")
        results.append("=" * 80)
        activity = query_service.get_person_activity(400)
        if activity:
            results.append(f"\nLegislative Activity - {activity.person.name}")
            if activity.person.club:
                results.append(f"Club: {activity.person.club}")
            results.append(f"Speeches: {activity.speechCount}")
            if activity.committees:
                results.append(f"Committees: {', '.join(activity.committees[:3])}")
            if activity.authoredPrints:
                results.append(f"\nAuthored Prints ({len(activity.authoredPrints)}):")
                for p in activity.authoredPrints[:3]:
                    results.append(f"  - Print {p.number}: {p.title}")
        
        # 7. list_clubs
        results.append("\n" + "=" * 80)
        results.append("7. list_clubs()")
        results.append("=" * 80)
        clubs = query_service.list_clubs()
        if clubs:
            results.append(f"\nParliamentary Clubs ({len(clubs)} total):\n")
            for i, club in enumerate(clubs, 1):
                results.append(f"{i}. {club.name} - {club.memberCount} members ({club.activeMembers} active)")
        
        # 8. list_clubs
        results.append("\n" + "=" * 80)
        results.append("8. list_clubs()")
        results.append("=" * 80)
        clubs = query_service.list_clubs()
        if clubs:
            results.append(f"\nParliamentary Clubs ({len(clubs)} total):\n")
            for i, club in enumerate(clubs, 1):
                results.append(f"{i}. {club.name} - {club.memberCount} members ({club.activeMembers} active)")
        
        # 8. search_by_topic_or_organization - by topic
        results.append("\n" + "=" * 80)
        results.append("8. search_by_topic_or_organization(query='Podatki', limit=3)")
        results.append("=" * 80)
        prints = query_service.search_prints_by_name(query="Podatki", limit=3)
        if prints:
            results.append(f"\nFound {len(prints)} prints:\n")
            for i, p in enumerate(prints, 1):
                results.extend(format_print(p, index=i))
        
        # 9. search_by_topic_or_organization - by organization
        results.append("\n" + "=" * 80)
        results.append("9. search_by_topic_or_organization(query='Ministerstwo Finansów', limit=3)")
        results.append("=" * 80)
        prints = query_service.search_prints_by_name(query="Ministerstwo Finansów", limit=3)
        if prints:
            results.append(f"\nFound {len(prints)} prints:\n")
            for i, p in enumerate(prints, 1):
                results.extend(format_print(p, index=i))
        
        # 10. search_by_topic_or_organization - another topic
        results.append("\n" + "=" * 80)
        results.append("10. search_by_topic_or_organization(query='Polityka pieniężna', limit=3)")
        results.append("=" * 80)
        prints = query_service.search_prints_by_name(query="Polityka pieniężna", limit=3)
        if prints:
            results.append(f"\nFound {len(prints)} prints:\n")
            for i, p in enumerate(prints, 1):
                results.extend(format_print(p, index=i))
        
        # 11. explore_node - Person
        results.append("\n" + "=" * 80)
        results.append("11. explore_node(node_type='Person', node_id='400', limit=5)")
        results.append("=" * 80)
        neighbors = query_service.get_node_neighbors("Person", "400", limit=5)
        if neighbors:
            results.append("\nNeighbors of Person '400':\n")
            for rel_type, data in list(neighbors.items())[:3]:
                results.append(f"[{rel_type}] → {data['neighborType']} (Total: {data['totalCount']})")
                for neighbor in data['neighbors'][:3]:
                    if 'name' in neighbor:
                        results.append(f"  - {neighbor['name']}")
                    elif 'title' in neighbor:
                        results.append(f"  - {neighbor.get('number', '?')}: {neighbor['title'][:50]}...")
        
        # 12. explore_node - Topic
        results.append("\n" + "=" * 80)
        results.append("12. explore_node(node_type='Topic', node_id='Podatki', limit=5)")
        results.append("=" * 80)
        neighbors = query_service.get_node_neighbors("Topic", "Podatki", limit=5)
        if neighbors:
            results.append("\nNeighbors of Topic 'Podatki':\n")
            for rel_type, data in list(neighbors.items())[:2]:
                results.append(f"[{rel_type}] → {data['neighborType']} (Total: {data['totalCount']})")
                for neighbor in data['neighbors'][:3]:
                    if 'title' in neighbor:
                        results.append(f"  - Print {neighbor.get('number', '?')}: {neighbor['title'][:50]}...")
        
        results.append("\n" + "=" * 80)
        results.append("END OF RESULTS")
        results.append("=" * 80)
        
    finally:
        neo4j_client.close()
    
    # Save to file
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(results))
    
    print("✅ Results saved to results.txt")
    print(f"   Total lines: {len(results)}")

if __name__ == "__main__":
    save_results()
