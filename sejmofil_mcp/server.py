"""Sejmofil Neo4j MCP Server - Main server implementation"""

import os
import sys
from mcp.server.fastmcp import FastMCP
from loguru import logger
from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from sejmofil_mcp.config import settings


def validate_api_key():
    """Validate API key if authorization is enabled"""
    # If no API key configured, allow access
    if not settings.API_KEY:
        logger.warning("No API key configured - authorization disabled")
        return True
    
    # Check for API_KEY environment variable from client
    client_api_key = os.getenv('API_KEY')
    
    if not client_api_key:
        logger.error("Authorization required: API_KEY environment variable not set")
        return False
    
    if client_api_key != settings.API_KEY:
        logger.error("Authorization failed: Invalid API key")
        return False
    
    logger.info("API key validated successfully")
    return True


# Validate API key before initializing server
if not validate_api_key():
    logger.error("Server startup aborted due to authentication failure")
    sys.exit(1)


# Initialize FastMCP server
mcp = FastMCP("Sejmofil Parliamentary Data")


# Connect to Neo4j on module load (for MCP Inspector compatibility)
try:
    neo4j_client.connect()
    logger.info("Neo4j connection established on module load")
except Exception as e:
    logger.error(f"Failed to connect to Neo4j on module load: {e}")


@mcp.tool()
def search_prints(query: str, limit: int = 10, status: str = "all") -> str:
    """
    Search for legislative processes (druki sejmowe) by topic or keywords.
    
    Returns ONLY initiating prints that start legislative processes, not supplementary documents.
    Uses AI semantic search when available, falls back to keyword search.
    
    Args:
        query: Search query in Polish (e.g., 'podatki', 'obrona', 'energia')
        limit: Max results (default: 10, max: 50)
        status: 'all', 'active' (in progress), or 'finished' (published/withdrawn)
    
    Returns:
        List with: print number, title, current stage, full summary, topics
    
    Examples:
        search_prints("podatki", status="active") - active tax legislation
        search_prints("obrona") - all defense-related processes
    """
    try:
        limit = min(limit, settings.MAX_LIMIT)
        
        # Validate status parameter
        if status not in ["all", "active", "finished"]:
            return f"Invalid status '{status}'. Must be 'all', 'active', or 'finished'"
        
        status_filter = None if status == "all" else status
        
        logger.info(f"Searching prints for: {query} (status: {status}, limit: {limit})")
        
        results = query_service.search_prints_by_query(query, limit, status_filter)
        
        if not results:
            return f"No prints found for query: {query} (status: {status})"
        
        # Format results
        output = f"Found {len(results)} prints for '{query}' (status: {status}):\n\n"
        for i, print_obj in enumerate(results, 1):
            output += f"{i}. Print {print_obj.number}\n"
            output += f"   Title: {print_obj.title}\n"
            if print_obj.currentStage:
                output += f"   Stage: {print_obj.currentStage}\n"
            if print_obj.summary:
                output += f"   Summary: {print_obj.summary}\n"
            if print_obj.topics:
                output += f"   Topics: {', '.join(print_obj.topics)}\n"
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in search_prints: {e}")
        return f"Error searching prints: {str(e)}"


@mcp.tool()
def explore_node(node_type: str, node_id: str, limit: int = 50) -> str:
    """
    Discover all connections of any entity in the parliamentary database.
    
    Shows what's related to: MPs, prints, topics, processes, clubs, or committees.
    Useful for understanding relationships and finding related information.
    
    Args:
        node_type: 'Person', 'Print', 'Topic', 'Process', 'Club', or 'Committee'
        node_id: Identifier (Person: ID number, Print/Process: number, Topic/Club: name, Committee: code)
        limit: Max items per relationship type (default: 50)
    
    Returns:
        All relationships grouped by type with sample connected entities
    
    Examples:
        explore_node("Person", "12345") - MP's connections
        explore_node("Topic", "Podatki") - all tax-related entities
        explore_node("Club", "PiS") - party members and activities
    """
    try:
        logger.info(f"Exploring node: {node_type} with ID {node_id}")
        
        neighbors = query_service.get_node_neighbors(node_type, node_id, limit)
        
        if not neighbors:
            return f"No neighbors found for {node_type} with ID '{node_id}' (or node not found)"
        
        output = f"Neighbors of {node_type} '{node_id}':\n"
        output += "=" * 50 + "\n\n"
        
        for rel_type, data in neighbors.items():
            output += f"[{rel_type}] → {data['neighborType']} (Total: {data['totalCount']})\n"
            
            # Show sample neighbors
            shown = min(10, len(data['neighbors']))
            for i, neighbor in enumerate(data['neighbors'][:shown], 1):
                # Format neighbor info based on type
                if 'name' in neighbor:
                    output += f"  {i}. {neighbor['name']}"
                    if 'club' in neighbor:
                        output += f" ({neighbor['club']})"
                    output += "\n"
                elif 'title' in neighbor:
                    output += f"  {i}. {neighbor.get('number', '?')}: {neighbor['title'][:60]}...\n"
                elif 'stageName' in neighbor:
                    output += f"  {i}. {neighbor['stageName']}"
                    if neighbor.get('date'):
                        output += f" ({neighbor['date']})"
                    output += "\n"
                elif 'speaker' in neighbor:
                    output += f"  {i}. {neighbor.get('speaker', 'Unknown')}: {neighbor.get('topic', '')[:50]}...\n"
                else:
                    output += f"  {i}. {neighbor}\n"
            
            if data['totalCount'] > shown:
                output += f"  ... and {data['totalCount'] - shown} more\n"
            
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in explore_node: {e}")
        return f"Error exploring node: {str(e)}"


@mcp.tool()
def get_process_details(print_number: str) -> str:
    """
    Get complete information about a legislative process using any related print number.
    
    Returns everything about the process: all associated prints, legislative journey,
    people involved, and organizations. Use this for deep analysis of legislation.
    
    Args:
        print_number: Any print number from the process (e.g., '1234')
    
    Returns:
        - Process number, title, and status (active/finished)
        - All prints in the process with summaries
        - Complete legislative stages timeline
        - All people mentioned (subjects) across all prints
        - All organizations involved
        - All related topics
    
    Note: One process can have multiple prints (initiating + amendments)
    """
    try:
        logger.info(f"Getting process details for print: {print_number}")
        
        details = query_service.get_process_details(print_number)
        
        if not details:
            return f"Process for print {print_number} not found"
        
        output = f"Process {details.processNumber} - Details\n"
        output += "=" * 50 + "\n\n"
        output += f"Title: {details.title}\n"
        output += f"Status: {details.status.upper()}\n\n"
        
        if details.currentStage:
            output += f"Current Stage: {details.currentStage}\n"
            if details.stageDate:
                output += f"Stage Date: {details.stageDate}\n"
            output += "\n"
        
        # Show all prints in the process
        if details.prints:
            output += f"Prints in Process ({len(details.prints)}):\n"
            for i, print_obj in enumerate(details.prints, 1):
                output += f"{i}. Print {print_obj.number}\n"
                output += f"   Title: {print_obj.title}\n"
                if print_obj.documentDate:
                    output += f"   Date: {print_obj.documentDate}\n"
                if print_obj.summary:
                    output += f"   Summary: {print_obj.summary[:200]}...\n"
                output += "\n"
        
        # Show all stages
        if details.allStages:
            output += f"Legislative Stages ({len(details.allStages)}):\n"
            for i, stage in enumerate(details.allStages, 1):
                output += f"{i}. {stage.stageName}"
                if stage.date:
                    output += f" ({stage.date})"
                if stage.type:
                    output += f" - {stage.type}"
                output += "\n"
            output += "\n"
        
        # Show all subjects
        if details.allSubjects:
            output += f"Subjects (People Mentioned) ({len(details.allSubjects)}):\n"
            for subject in details.allSubjects[:20]:  # Show first 20
                output += f"  - {subject}\n"
            if len(details.allSubjects) > 20:
                output += f"  ... and {len(details.allSubjects) - 20} more\n"
            output += "\n"
        
        # Show all organizations
        if details.allOrganizations:
            output += f"Organizations Involved ({len(details.allOrganizations)}):\n"
            for org in details.allOrganizations[:20]:  # Show first 20
                output += f"  - {org}\n"
            if len(details.allOrganizations) > 20:
                output += f"  ... and {len(details.allOrganizations) - 20} more\n"
            output += "\n"
        
        # Show all topics
        if details.allTopics:
            output += f"Topics ({len(details.allTopics)}):\n"
            for topic in details.allTopics:
                output += f"  - {topic}\n"
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_process_details: {e}")
        return f"Error getting process details: {str(e)}"


@mcp.tool()
def get_process_status(process_number: str) -> str:
    """
    Check if a legislative process is still in progress or completed.
    
    Analyzes legislative stages to determine current status.
    Use when you need quick status check without full details.
    
    Args:
        process_number: The process number
    
    Returns:
        Status (active/finished/unknown), current stage, all stages with dates
    
    Note: Finished means published or withdrawn. Active means still being processed.
    """
    try:
        logger.info(f"Checking process status: {process_number}")
        
        status = query_service.get_process_status(process_number)
        
        if not status:
            return f"Process {process_number} not found"
        
        output = f"Process {status.processNumber} - Status\n"
        output += "=" * 50 + "\n\n"
        output += f"Status: {status.status.upper()}\n"
        
        if status.currentStage:
            output += f"Current Stage: {status.currentStage}\n"
        
        if status.stageDate:
            output += f"Stage Date: {status.stageDate}\n"
        
        if status.allStages:
            output += f"\nAll Stages ({len(status.allStages)}):\n"
            for stage in status.allStages:
                output += f"  {stage.number or '?'}. {stage.stageName}"
                if stage.date:
                    output += f" ({stage.date})"
                if stage.type:
                    output += f" - {stage.type}"
                output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_process_status: {e}")
        return f"Error checking process status: {str(e)}"


@mcp.tool()
def find_mp_by_name(name: str) -> str:
    """
    Find members of parliament (MPs) by name or partial name.
    
    Searches across different Polish name forms (cases). Returns all matches.
    
    Args:
        name: Full or partial name (e.g., 'Kowalski', 'Jan', 'Tusk')
    
    Returns:
        List of MPs with: name, party (club), role, ID, active status
    
    Tip: Use returned ID with get_mp_activity() for detailed information
    """
    try:
        logger.info(f"Finding MP by name: {name}")
        
        results = query_service.find_person_by_name(name)
        
        if not results:
            return f"No MPs found matching: {name}"
        
        output = f"Found {len(results)} MPs matching '{name}':\n\n"
        for i, person in enumerate(results, 1):
            output += f"{i}. {person.name}"
            if person.club:
                output += f" ({person.club})"
            if person.role:
                output += f"\n   Role: {person.role}"
            if person.id:
                output += f"\n   ID: {person.id}"
            output += f"\n   Active: {'Yes' if person.active else 'No'}\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in find_mp_by_name: {e}")
        return f"Error finding MP: {str(e)}"


@mcp.tool()
def get_mp_activity(person_id: int) -> str:
    """
    Get complete legislative activity profile for an MP.
    
    Shows what the MP has done: authored legislation, speeches, committees, 
    and prints they're mentioned in.
    
    Args:
        person_id: MP's ID number (get from find_mp_by_name)
    
    Returns:
        - Basic info (name, party, role)
        - Authored prints with topics
        - Prints where they're mentioned (subject)
        - Speech count
        - Committee memberships
    """
    try:
        logger.info(f"Getting activity for person ID: {person_id}")
        
        activity = query_service.get_person_activity(person_id)
        
        if not activity:
            return f"MP with ID {person_id} not found"
        
        output = f"Legislative Activity - {activity.person.name}\n"
        output += "=" * 50 + "\n\n"
        
        if activity.person.club:
            output += f"Club: {activity.person.club}\n"
        if activity.person.role:
            output += f"Role: {activity.person.role}\n"
        
        output += f"\nSpeeches: {activity.speechCount}\n"
        
        if activity.committees:
            output += f"\nCommittees ({len(activity.committees)}):\n"
            for committee in activity.committees:
                output += f"  - {committee}\n"
        
        if activity.authoredPrints:
            output += f"\nAuthored Prints ({len(activity.authoredPrints)}):\n"
            for print_obj in activity.authoredPrints[:5]:  # Show first 5
                output += f"  - Print {print_obj.number}: {print_obj.title}\n"
                if print_obj.topics:
                    output += f"    Topics: {', '.join(print_obj.topics)}\n"
        
        if activity.subjectPrints:
            output += f"\nPrints About Them ({len(activity.subjectPrints)}):\n"
            for print_obj in activity.subjectPrints[:5]:  # Show first 5
                output += f"  - Print {print_obj.number}: {print_obj.title}\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_mp_activity: {e}")
        return f"Error getting MP activity: {str(e)}"





@mcp.tool()
def get_club_statistics(club_name: str) -> str:
    """
    Get comprehensive statistics for a parliamentary party/club.
    
    Analyzes party's overall legislative activity, size, and engagement metrics.
    
    Args:
        club_name: Party name (e.g., 'PiS', 'Platforma Obywatelska', 'Lewica')
    
    Returns:
        - Membership (total and active MPs)
        - Legislative output (total/active/finished prints)
        - Engagement (votes cast, speeches, committee positions)
    
    Tip: Use list_clubs() to see all available party names
    """
    try:
        logger.info(f"Getting statistics for club: {club_name}")
        
        stats = query_service.get_club_statistics(club_name)
        
        if not stats:
            return f"Club '{club_name}' not found"
        
        output = f"Club Statistics - {stats.name}\n"
        output += "=" * 50 + "\n\n"
        
        output += f"Members: {stats.memberCount}\n"
        output += f"Active Members: {stats.activeMembers}\n"
        
        output += f"\nLegislative Activity:\n"
        output += f"  Total Authored Prints: {stats.authoredPrints}\n"
        output += f"  Active Prints: {stats.activePrints}\n"
        output += f"  Finished Prints: {stats.finishedPrints}\n"
        
        output += f"\nParliamentary Engagement:\n"
        output += f"  Votes Cast: {stats.totalVotes}\n"
        output += f"  Speeches: {stats.speechCount}\n"
        output += f"  Committee Positions: {stats.committeePositions}\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_club_statistics: {e}")
        return f"Error getting club statistics: {str(e)}"


@mcp.tool()
def list_clubs() -> str:
    """
    List all parliamentary parties/clubs with membership information.
    
    Shows all political groups in parliament, ordered by size (largest first).
    
    Returns:
        All clubs with: name, total members, active members
    
    Use: Get party names for get_club_statistics() or to understand parliament composition
    """
    try:
        logger.info("Listing all parliamentary clubs")
        
        clubs = query_service.list_clubs()
        
        if not clubs:
            return "No clubs found in the database"
        
        output = f"Parliamentary Clubs ({len(clubs)} total)\n"
        output += "=" * 50 + "\n\n"
        
        for i, club in enumerate(clubs, 1):
            output += f"{i}. {club.name}\n"
            output += f"   Members: {club.memberCount}"
            if club.activeMembers > 0:
                output += f" (Active: {club.activeMembers})"
            output += "\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in list_clubs: {e}")
        return f"Error listing clubs: {str(e)}"





def run_server():
    """Run the MCP server"""
    logger.info("Starting Sejmofil Neo4j MCP Server")
    
    # Connect to Neo4j
    try:
        neo4j_client.connect()
        logger.info("Neo4j connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        raise
    
    try:
        # Run the server with SSE transport
        mcp.run(transport="sse")
    finally:
        # Cleanup
        neo4j_client.close()
        logger.info("Server shutdown complete")


# Expose the ASGI app from FastMCP for Uvicorn (using SSE transport)
app = mcp.sse_app


if __name__ == "__main__":
    run_server()
