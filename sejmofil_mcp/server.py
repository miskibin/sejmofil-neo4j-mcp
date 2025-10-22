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
def search_active_prints_by_topic(topic: str, limit: int = 10) -> str:
    """
    Find currently processed (active) parliamentary prints on a specific topic using semantic search.
    
    This tool searches for legislative prints (druki sejmowe) that are currently being processed
    in the parliament and match the given topic. It uses semantic search via embeddings to find
    relevant prints even when exact keywords don't match.
    
    Args:
        topic: Topic to search for in Polish (e.g., 'podatki', 'obrona narodowa', 'edukacja', 'zdrowie')
        limit: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        JSON string with list of active prints including:
        - Print number and title
        - Summary of the print
        - Current legislative stage
        - Related topics
        - Document date
    
    Examples:
        - "podatki" - finds tax-related prints
        - "obrona narodowa" - finds national defense prints
        - "energia odnawialna" - finds renewable energy prints
    """
    try:
        limit = min(limit, settings.MAX_LIMIT)
        logger.info(f"Searching active prints for topic: {topic} (limit: {limit})")
        
        results = query_service.search_active_prints_by_topic(topic, limit)
        
        if not results:
            return f"No active prints found for topic: {topic}"
        
        # Format results
        output = f"Found {len(results)} active prints for topic '{topic}':\n\n"
        for i, print_obj in enumerate(results, 1):
            output += f"{i}. Print {print_obj.number}\n"
            output += f"   Title: {print_obj.title}\n"
            if print_obj.summary:
                output += f"   Summary: {print_obj.summary[:200]}...\n"
            if print_obj.currentStage:
                output += f"   Current Stage: {print_obj.currentStage}\n"
            if print_obj.topics:
                output += f"   Topics: {', '.join(print_obj.topics)}\n"
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in search_active_prints_by_topic: {e}")
        return f"Error searching prints: {str(e)}"


@mcp.tool()
def get_print_details(print_number: str) -> str:
    """
    Get comprehensive information about a specific parliamentary print.
    
    Retrieves detailed information about a legislative print including authors,
    topics, organizations involved, current legislative stage, and comments.
    
    Args:
        print_number: The print number to look up (e.g., '1234', '567')
    
    Returns:
        JSON string with detailed print information including:
        - Full metadata (title, dates, document type)
        - Authors and subjects
        - Related topics and organizations
        - Current process stage
        - Attachments
    """
    try:
        logger.info(f"Getting details for print: {print_number}")
        
        details = query_service.get_print_details(print_number)
        
        if not details:
            return f"Print {print_number} not found"
        
        output = f"Print {details.number} - Details\n"
        output += "=" * 50 + "\n\n"
        output += f"Title: {details.title}\n\n"
        
        if details.summary:
            output += f"Summary:\n{details.summary}\n\n"
        
        if details.documentType:
            output += f"Document Type: {details.documentType}\n"
        
        if details.documentDate:
            output += f"Document Date: {details.documentDate}\n"
        
        if details.changeDate:
            output += f"Change Date: {details.changeDate}\n"
        
        if details.processNumber:
            output += f"Process Number: {details.processNumber}\n"
        
        if details.authors:
            output += f"\nAuthors:\n"
            for author in details.authors:
                output += f"  - {author}\n"
        
        if details.subjects:
            output += f"\nSubjects (people mentioned):\n"
            for subject in details.subjects:
                output += f"  - {subject}\n"
        
        if details.topics:
            output += f"\nTopics:\n"
            for topic in details.topics:
                output += f"  - {topic}\n"
        
        if details.organizations:
            output += f"\nOrganizations:\n"
            for org in details.organizations:
                output += f"  - {org}\n"
        
        if details.currentStage:
            output += f"\nCurrent Legislative Stage: {details.currentStage}\n"
            if details.stageDate:
                output += f"Stage Date: {details.stageDate}\n"
        
        if details.processNumber:
            output += f"\nProcess Number: {details.processNumber}\n"
        
        # Get comments
        comments = query_service.get_print_comments(print_number)
        if comments:
            output += f"\nComments ({len(comments)}):\n"
            for comment in comments[:5]:  # Show first 5
                output += f"  - {comment.author}"
                if comment.organization:
                    output += f" ({comment.organization})"
                if comment.sentiment:
                    output += f" - {comment.sentiment}"
                output += f"\n    {comment.summary[:150]}...\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_print_details: {e}")
        return f"Error getting print details: {str(e)}"


@mcp.tool()
def get_process_status(process_number: str) -> str:
    """
    Check if a legislative process is currently active or has finished.
    
    Analyzes the legislative process stages to determine if it's still being
    processed or has reached a final stage (published, rejected, or withdrawn).
    
    Args:
        process_number: The process number to check
    
    Returns:
        JSON string with process status information:
        - Status (active/finished/unknown)
        - Current stage name
        - All stages in the process
        - Stage dates
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
    Find members of parliament by name.
    
    Searches for MPs using fulltext search on various name forms
    (nominative, accusative, genitive cases in Polish).
    
    Args:
        name: MP name or partial name to search for (e.g., 'Kowalski', 'Jan Kowalski')
    
    Returns:
        JSON string with list of matching MPs including:
        - Full name
        - Parliamentary club
        - Role
        - Active status
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
    Get legislative activity for a member of parliament.
    
    Retrieves comprehensive information about an MP's legislative work including
    authored prints, prints they're mentioned in, speeches, and committee memberships.
    
    Args:
        person_id: The MP's ID number
    
    Returns:
        JSON string with MP's activity including:
        - Basic info (name, club, role)
        - Authored prints
        - Prints about them (subject)
        - Number of speeches
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
def get_similar_topics(topic_name: str, limit: int = 5) -> str:
    """
    Find topics semantically similar to a given topic.
    
    Uses embeddings and cosine similarity to find related topics that might
    be relevant for expanding search scope or discovering related legislation.
    
    Args:
        topic_name: Topic name to find similar topics for (must match exactly)
        limit: Maximum number of similar topics to return (default: 5)
    
    Returns:
        JSON string with list of similar topics including:
        - Topic name
        - Description
        - Number of related prints
        - Similarity score
    """
    try:
        logger.info(f"Finding similar topics for: {topic_name}")
        
        results = query_service.get_similar_topics(topic_name, limit)
        
        if not results:
            return f"No similar topics found for: {topic_name}"
        
        output = f"Topics similar to '{topic_name}':\n\n"
        for i, topic in enumerate(results, 1):
            output += f"{i}. {topic.name}"
            if topic.similarity:
                output += f" (similarity: {topic.similarity:.2f})"
            output += "\n"
            if topic.description:
                output += f"   {topic.description}\n"
            if topic.printCount:
                output += f"   Prints: {topic.printCount}\n"
            output += "\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_similar_topics: {e}")
        return f"Error finding similar topics: {str(e)}"


@mcp.tool()
def get_topic_statistics(topic_name: str) -> str:
    """
    Get statistics about a parliamentary topic.
    
    Provides overview statistics about how many prints are associated with
    a topic and their current status (active vs finished processes).
    
    Args:
        topic_name: Topic name to get statistics for
    
    Returns:
        JSON string with topic statistics:
        - Topic name and description
        - Total number of prints
        - Number of active prints
        - Number of finished prints
    """
    try:
        logger.info(f"Getting statistics for topic: {topic_name}")
        
        stats = query_service.get_topic_statistics(topic_name)
        
        if not stats:
            return f"Topic '{topic_name}' not found"
        
        output = f"Topic Statistics - {stats.get('name', topic_name)}\n"
        output += "=" * 50 + "\n\n"
        
        if stats.get('description'):
            output += f"Description: {stats['description']}\n\n"
        
        output += f"Total Prints: {stats.get('totalPrints', 0)}\n"
        output += f"Active Prints: {stats.get('activePrints', 0)}\n"
        output += f"Finished Prints: {stats.get('finishedPrints', 0)}\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_topic_statistics: {e}")
        return f"Error getting topic statistics: {str(e)}"


@mcp.tool()
def get_club_statistics(club_name: str) -> str:
    """
    Get comprehensive statistics about a parliamentary club (political party/group).
    
    Retrieves detailed statistics about a club including membership, legislative
    activity (authored prints), voting participation, speeches, and committee
    involvement.
    
    Args:
        club_name: Club name to get statistics for (e.g., 'PiS', 'Platforma Obywatelska', 'Lewica')
    
    Returns:
        JSON string with club statistics including:
        - Club name
        - Total members and active members
        - Number of authored prints (active and finished)
        - Total votes cast by club members
        - Total speeches made by club members
        - Number of committee positions held
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
    List all parliamentary clubs (political parties/groups).
    
    Retrieves a list of all parliamentary clubs currently in the database,
    showing member counts and active member information.
    
    Returns:
        Formatted string with list of all clubs including:
        - Club name
        - Total number of members
        - Number of active members
        - Ordered by membership size (largest first)
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


@mcp.tool()
def search_all(query: str, limit: int = 10) -> str:
    """
    Search across all entity types (prints, MPs, topics).
    
    Performs a comprehensive search across the database to find relevant
    prints and members of parliament matching the query.
    
    Args:
        query: Search query in Polish
        limit: Maximum results per category (default: 10)
    
    Returns:
        JSON string with search results grouped by type:
        - Prints (with summaries and relevance scores)
        - MPs (with clubs and roles)
    """
    try:
        logger.info(f"Searching all entities for: {query}")
        
        results = query_service.search_all(query, limit)
        
        output = f"Search Results for '{query}'\n"
        output += "=" * 50 + "\n\n"
        
        # Prints
        if results.get("prints"):
            output += f"PRINTS ({len(results['prints'])}):\n\n"
            for i, item in enumerate(results["prints"][:limit], 1):
                output += f"{i}. {item.title} (ID: {item.id})\n"
                if item.description:
                    output += f"   {item.description[:150]}...\n"
                output += "\n"
        
        # Persons
        if results.get("persons"):
            output += f"\nMEMBERS OF PARLIAMENT ({len(results['persons'])}):\n\n"
            for i, item in enumerate(results["persons"][:limit], 1):
                output += f"{i}. {item.title}"
                if item.description:
                    output += f" - {item.description}"
                output += "\n"
        
        if not results.get("prints") and not results.get("persons"):
            output += "No results found.\n"
        
        return output
    except Exception as e:
        logger.error(f"Error in search_all: {e}")
        return f"Error searching: {str(e)}"


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
