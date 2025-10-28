"""Sejmofil Neo4j MCP Server - Main server implementation"""

import os
import sys
from mcp.server.fastmcp import FastMCP
from loguru import logger
from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.queries import query_service
from sejmofil_mcp.config import settings
from sejmofil_mcp.models import PrintShort


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


def format_print_output(print_obj: PrintShort, index: int = None) -> str:
    """
    Format a single print object for consistent output across all functions.
    
    Args:
        print_obj: PrintShort object to format
        index: Optional index number for the print in a list
        
    Returns:
        Formatted string representation of the print
    """
    output = ""
    
    # Add index if provided
    if index is not None:
        output += f"{index}. Print {print_obj.number}\n"
    else:
        output += f"Print {print_obj.number}\n"
    
    # Title
    output += f"   {print_obj.title}\n"
    
    # Document date (without timestamp)
    if print_obj.documentDate:
        date_only = print_obj.documentDate.split('T')[0] if 'T' in print_obj.documentDate else print_obj.documentDate
        output += f"   Date: {date_only}\n"
    
    # Current stage with stage date (without timestamp)
    if print_obj.currentStage:
        stage_info = f"   Stage: {print_obj.currentStage}"
        if print_obj.stageDate:
            stage_date_only = print_obj.stageDate.split('T')[0] if 'T' in print_obj.stageDate else print_obj.stageDate
            stage_info += f" ({stage_date_only})"
        output += stage_info + "\n"
    
    # Summary
    if print_obj.summary:
        output += f"   {print_obj.summary}\n"
    
    return output


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
    Search for legislative prints by keywords using semantic AI search.
    Returns only initiating prints (process-starting documents).
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
        
        # Format results using helper function
        output = f"Found {len(results)} prints for '{query}' (status: {status}):\n\n"
        for i, print_obj in enumerate(results, 1):
            output += format_print_output(print_obj, index=i)
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in search_prints: {e}")
        return f"Error searching prints: {str(e)}"


@mcp.tool()
def explore_node(node_type: str, node_id: str, limit: int = 50) -> str:
    """
    Discover all connections for any entity (MPs, prints, topics, processes, clubs, committees).
    Shows relationships grouped by type with connected entities.
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
    Shows all prints, stages, people involved, organizations, and topics.
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
            output += f"Prints ({len(details.prints)}):\n"
            for i, print_obj in enumerate(details.prints, 1):
                output += f"\n{i}. Print {print_obj.number}\n"
                output += f"   {print_obj.title}\n"
                if print_obj.documentDate:
                    output += f"   Date: {print_obj.documentDate}\n"
                if print_obj.summary:
                    output += f"   {print_obj.summary}\n"
            output += "\n"
        
        # Show all stages
        if details.allStages:
            output += f"Stages ({len(details.allStages)}):\n"
            for i, stage in enumerate(details.allStages, 1):
                output += f"{i}. {stage.stageName}"
                if stage.date:
                    output += f" ({stage.date})"
                output += "\n"
            output += "\n"
        
        # Show all subjects
        if details.allSubjects:
            output += f"People Mentioned ({len(details.allSubjects)}):\n"
            output += f"  {', '.join(details.allSubjects[:10])}\n"
            if len(details.allSubjects) > 10:
                output += f"  ... and {len(details.allSubjects) - 10} more\n"
            output += "\n"
        
        # Show all organizations
        if details.allOrganizations:
            output += f"Organizations ({len(details.allOrganizations)}):\n"
            output += f"  {', '.join(details.allOrganizations[:10])}\n"
            if len(details.allOrganizations) > 10:
                output += f"  ... and {len(details.allOrganizations) - 10} more\n"
            output += "\n"
        
        # Show all topics
        if details.allTopics:
            output += f"Topics: {', '.join(details.allTopics)}\n\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_process_details: {e}")
        return f"Error getting process details: {str(e)}"


@mcp.tool()
def get_process_status(process_number: str) -> str:
    """
    Check if a legislative process is active or finished.
    Shows current status, latest stage, and all historical stages.
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
            output += f"\nStages ({len(status.allStages)}):\n"
            for stage in status.allStages:
                output += f"  {stage.stageName}"
                if stage.date:
                    output += f" ({stage.date})"
                output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_process_status: {e}")
        return f"Error checking process status: {str(e)}"


@mcp.tool()
def find_mp_by_name(name: str) -> str:
    """
    Find members of parliament by name or partial name.
    Returns matching MPs with party, role, ID, and active status.
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
            output += f" - ID: {person.id}\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in find_mp_by_name: {e}")
        return f"Error finding MP: {str(e)}"


@mcp.tool()
def get_mp_activity(person_id: int) -> str:
    """
    Get legislative activity for an MP.
    Shows authored prints, prints they're mentioned in, speeches, and committees.
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
        
        output += f"Speeches: {activity.speechCount}\n"
        
        if activity.committees:
            output += f"Committees: {', '.join(activity.committees[:3])}\n"
            if len(activity.committees) > 3:
                output += f"... and {len(activity.committees) - 3} more\n"
        
        if activity.authoredPrints:
            output += f"\nAuthored Prints ({len(activity.authoredPrints)}):\n"
            for print_obj in activity.authoredPrints[:3]:
                output += f"  - Print {print_obj.number}: {print_obj.title}\n"
            if len(activity.authoredPrints) > 3:
                output += f"  ... and {len(activity.authoredPrints) - 3} more\n"
        
        if activity.subjectPrints:
            output += f"\nPrints About Them ({len(activity.subjectPrints)}):\n"
            for print_obj in activity.subjectPrints[:3]:
                output += f"  - Print {print_obj.number}: {print_obj.title}\n"
            if len(activity.subjectPrints) > 3:
                output += f"  ... and {len(activity.subjectPrints) - 3} more\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_mp_activity: {e}")
        return f"Error getting MP activity: {str(e)}"





@mcp.tool()
def list_clubs() -> str:
    """
    List all parliamentary parties/clubs with membership information.
    Ordered by size (largest first).
    """
    try:
        logger.info("Listing all parliamentary clubs")
        
        clubs = query_service.list_clubs()
        
        if not clubs:
            return "No clubs found in the database"
        
        output = f"Parliamentary Clubs ({len(clubs)} total)\n"
        output += "=" * 50 + "\n\n"
        
        for i, club in enumerate(clubs, 1):
            output += f"{i}. {club.name} - {club.memberCount} members"
            if club.activeMembers > 0:
                output += f" ({club.activeMembers} active)"
            output += "\n"
        
        return output
        
        return output
    except Exception as e:
        logger.error(f"Error in list_clubs: {e}")
        return f"Error listing clubs: {str(e)}"


@mcp.tool()
def search_by_topic_or_organization(
    query: str, 
    limit: int = 10,
    status: str = "all",
    only_initiating: bool = True
) -> str:
    """
    Find prints related to a specific topic or organization by name.
    Searches both topics and organizations simultaneously.
    """
    try:
        # Enforce max limit of 20
        limit = min(limit, 20)
        
        # Validate that query is provided
        if not query:
            return "Error: 'query' parameter must be provided"
        
        # Validate status parameter
        if status not in ["all", "active", "finished"]:
            return f"Invalid status '{status}'. Must be 'all', 'active', or 'finished'"
        
        status_filter = None if status == "all" else status
        
        logger.info(f"Searching prints by name='{query}' (status: {status}, limit: {limit}, only_initiating: {only_initiating})")
        
        results = query_service.search_prints_by_name(
            query=query,
            limit=limit,
            status_filter=status_filter,
            only_process_print=only_initiating
        )
        
        if not results:
            return f"No prints found for '{query}' (status: {status})"
        
        # Format results using helper function
        output = f"Found {len(results)} prints for '{query}' (status: {status}):\n\n"
        for i, print_obj in enumerate(results, 1):
            output += format_print_output(print_obj, index=i)
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in search_by_topic_or_organization: {e}")
        return f"Error searching prints: {str(e)}"



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
