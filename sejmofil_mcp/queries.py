"""Cypher queries for Neo4j database"""

from typing import List, Dict, Any, Optional
from loguru import logger
from sejmofil_mcp.neo4j_client import neo4j_client
from sejmofil_mcp.embeddings import embeddings_service
from sejmofil_mcp.models import (
    PrintShort, PrintDetail, Comment, Person, PersonActivity,
    Topic, VotingResult, ProcessStatus, ProcessStage, SearchResult, Club, ClubStatistics,
    ProcessDetail
)
from sejmofil_mcp.config import settings


class QueryService:
    """Service for executing Neo4j queries"""
    
    def search_prints_by_query(
        self, 
        query_text: str, 
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[PrintShort]:
        """
        Search for prints using semantic or fulltext search
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results
            status_filter: Optional filter - 'active', 'finished', or None for all
            
        Returns:
            List of prints matching the query
        """
        if not embeddings_service.is_available():
            logger.warning("Embeddings service not available, falling back to fulltext search")
            return self._search_prints_fulltext(query_text, limit, status_filter)
        
        # Generate embedding for the query
        embedding = embeddings_service.generate_embedding(query_text)
        
        query = """
        // Vector search on prints
        CALL db.index.vector.queryNodes('printEmbeddingIndex', $limit * 2, $embedding)
        YIELD node as print, score
        WHERE print.summary IS NOT NULL
          AND print.number IN print.processPrint
        
        // Get process and stages
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH print, score, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        // Get latest stage per print
        WITH print, score, process, COLLECT(stage)[0] as latestStage
        """
        
        # Add status filter if specified
        if status_filter == 'active':
            query += """
            WHERE process IS NULL
               OR latestStage IS NULL
               OR latestStage.type IS NULL
               OR NOT (latestStage.type IN ['PUBLICATION', 'WITHDRAWAL'])
            """
        elif status_filter == 'finished':
            query += """
            WHERE latestStage.type IN ['PUBLICATION', 'WITHDRAWAL']
            """
        
        query += """
        // Enrich with topics
        OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
        WITH print, score, latestStage, COLLECT(DISTINCT topic.name) as topics
        
        RETURN 
          print.number as number,
          print.title as title,
          print.summary as summary,
          print.documentDate as documentDate,
          latestStage.stageName as currentStage,
          latestStage.date as stageDate,
          topics,
          score
        ORDER BY score ASC, print.documentDate DESC
        LIMIT $limit
        """
        
        results = neo4j_client.execute_read_query(query, {
            "embedding": embedding,
            "limit": limit
        })
        
        return [PrintShort(**r) for r in results]
    
    def _search_prints_fulltext(
        self, 
        query_text: str, 
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> List[PrintShort]:
        """Fallback fulltext search for prints"""
        
        query = """
        CALL db.index.fulltext.queryNodes("print_content", $query) 
        YIELD node as print, score
        WHERE print.summary IS NOT NULL
          AND print.number IN print.processPrint
        
        // Get process status
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH print, score, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        WITH print, score, process, COLLECT(stage)[0] as latestStage
        """
        
        # Add status filter if specified
        if status_filter == 'active':
            query += """
            WHERE process IS NULL
               OR latestStage IS NULL
               OR latestStage.type IS NULL
               OR NOT (latestStage.type IN ['PUBLICATION', 'WITHDRAWAL'])
            """
        elif status_filter == 'finished':
            query += """
            WHERE latestStage.type IN ['PUBLICATION', 'WITHDRAWAL']
            """
        
        query += """
        OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
        WITH print, score, latestStage, COLLECT(DISTINCT topic.name) as topics
        
        RETURN 
          print.number as number,
          print.title as title,
          print.summary as summary,
          print.documentDate as documentDate,
          latestStage.stageName as currentStage,
          latestStage.date as stageDate,
          topics,
          score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        results = neo4j_client.execute_read_query(query, {
            "query": query_text,
            "limit": limit
        })
        
        return [PrintShort(**r) for r in results]
    
    def get_print_details(self, print_number: str) -> Optional[PrintDetail]:
        """
        Get comprehensive details about a specific print
        
        Args:
            print_number: Print number to look up
            
        Returns:
            Detailed print information or None if not found
        """
        query = """
        MATCH (print:Print {number: $printNumber})
        
        // Get process and latest stage
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        WITH print, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        WITH print, process, COLLECT(stage)[0] as latestStage
        
        // Get all authors at once (both Person and Committee)
        OPTIONAL MATCH (personAuthor:Person)-[:AUTHORED]->(print)
        OPTIONAL MATCH (committeeAuthor:Committee)-[:AUTHORED]->(print)
        WITH print, process, latestStage, 
             COLLECT(DISTINCT personAuthor.firstLastName) + COLLECT(DISTINCT committeeAuthor.name) as authors
        
        // Get subjects
        OPTIONAL MATCH (subject:Person)-[:SUBJECT]->(print)
        WITH print, process, latestStage, authors, COLLECT(DISTINCT subject.firstLastName) as subjects
        
        // Get topics
        OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
        WITH print, process, latestStage, authors, subjects, COLLECT(DISTINCT topic.name) as topics
        
        // Get organizations
        OPTIONAL MATCH (print)-[:REFERS_TO]->(org:Organization)
        WITH print, process, latestStage, authors, subjects, topics, COLLECT(DISTINCT org.name) as organizations
        
        RETURN 
          print.number as number,
          print.title as title,
          print.summary as summary,
          print.documentDate as documentDate,
          print.changeDate as changeDate,
          CASE 
            WHEN print.processPrint[0] = print.number THEN 'initiating'
            ELSE 'supplementary'
          END as documentType,
          authors,
          subjects,
          topics,
          organizations,
          latestStage.stageName as currentStage,
          latestStage.date as stageDate,
          process.number as processNumber,
          print.attachments as attachments
        """
        
        results = neo4j_client.execute_read_query(query, {"printNumber": print_number})
        
        if not results:
            return None
        
        return PrintDetail(**results[0])
    
    def get_process_details(self, print_number: str) -> Optional[ProcessDetail]:
        """
        Get comprehensive details about a legislative process including all related prints
        
        Args:
            print_number: Any print number from the process to look up
            
        Returns:
            Detailed process information with all prints, stages, subjects, and organizations
        """
        
        query = """
        // Find the print and its process
        MATCH (print:Print {number: $printNumber})
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        
        // If no process found, this print doesn't have one
        WITH print, process
        WHERE process IS NOT NULL
        
        // Get all prints in this process
        OPTIONAL MATCH (processPrint:Print)-[:IS_SOURCE_OF]->(process)
        
        // Get all stages
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        WITH print, process, processPrint, stage
        ORDER BY stage.date DESC, stage.number DESC
        WITH print, process, 
             COLLECT(DISTINCT processPrint) as allProcessPrints,
             COLLECT(stage) as allStages,
             COLLECT(stage)[0] as latestStage
        
        // Determine process status
        WITH print, process, allProcessPrints, allStages, latestStage,
             CASE 
               WHEN latestStage IS NULL THEN 'unknown'
               WHEN latestStage.type IN ['PUBLICATION', 'WITHDRAWAL'] THEN 'finished'
               ELSE 'active'
             END as status
        
        // Get all subjects from all prints in the process
        UNWIND allProcessPrints as pp
        OPTIONAL MATCH (subject:Person)-[:SUBJECT]->(pp)
        WITH print, process, allProcessPrints, allStages, latestStage, status,
             COLLECT(DISTINCT subject.firstLastName) as allSubjects
        
        // Get all organizations from all prints in the process
        UNWIND allProcessPrints as pp2
        OPTIONAL MATCH (pp2)-[:REFERS_TO]->(org:Organization)
        WITH print, process, allProcessPrints, allStages, latestStage, status, allSubjects,
             COLLECT(DISTINCT org.name) as allOrganizations
        
        // Get all topics from all prints in the process
        UNWIND allProcessPrints as pp3
        OPTIONAL MATCH (pp3)-[:REFERS_TO]->(topic:Topic)
        WITH print, process, allProcessPrints, allStages, latestStage, status, 
             allSubjects, allOrganizations,
             COLLECT(DISTINCT topic.name) as allTopics
        
        // Format print details
        WITH process, allStages, latestStage, status, allSubjects, allOrganizations, allTopics,
             [p in allProcessPrints | {
               number: p.number,
               title: p.title,
               summary: p.summary,
               documentDate: p.documentDate
             }] as printDetails
        
        RETURN 
          process.number as processNumber,
          process.title as title,
          status,
          latestStage.stageName as currentStage,
          latestStage.date as stageDate,
          [s in allStages | {
            stageName: s.stageName,
            date: s.date,
            number: s.number,
            type: s.type
          }] as allStages,
          printDetails as prints,
          allSubjects,
          allOrganizations,
          allTopics
        """
        
        results = neo4j_client.execute_read_query(query, {"printNumber": print_number})
        
        if not results:
            return None
        
        # Convert prints to PrintShort objects
        result = results[0]
        prints_data = result.get('prints', [])
        prints = [PrintShort(**{k: v for k, v in p.items() if k in ['number', 'title', 'summary', 'documentDate']}) 
                  for p in prints_data if p]
        
        # Convert stages to ProcessStage objects
        stages_data = result.get('allStages', [])
        stages = [ProcessStage(**{k: v for k, v in s.items() if k in ['stageName', 'date', 'number', 'type']}) 
                  for s in stages_data if s]
        
        return ProcessDetail(
            processNumber=result['processNumber'],
            title=result.get('title', ''),
            status=result['status'],
            currentStage=result.get('currentStage'),
            stageDate=result.get('stageDate'),
            allStages=stages,
            prints=prints,
            allSubjects=[s for s in result.get('allSubjects', []) if s],
            allOrganizations=[o for o in result.get('allOrganizations', []) if o],
            allTopics=[t for t in result.get('allTopics', []) if t]
        )
    
    def get_print_comments(self, print_number: str) -> List[Comment]:
        """
        Get comments on a specific print
        
        Args:
            print_number: Print number
            
        Returns:
            List of comments with sentiment analysis
        """
        query = """
        MATCH (person:Person)-[r:COMMENTS]->(print:Print {number: $printNumber})
        OPTIONAL MATCH (person)-[:REPRESENTS]->(org:Organization)
        
        WITH DISTINCT r.summary AS summary, person, org, r
        WITH summary, 
             COLLECT(DISTINCT person.firstLastName)[0] AS author,
             COLLECT(DISTINCT org.name)[0] AS organization,
             COLLECT(DISTINCT r.sentiment)[0] AS sentiment
        
        RETURN author, organization, sentiment, summary
        """
        
        results = neo4j_client.execute_read_query(query, {"printNumber": print_number})
        return [Comment(**r) for r in results]
    
    def get_process_status(self, process_number: str) -> Optional[ProcessStatus]:
        """
        Check if a legislative process is active or finished
        
        Args:
            process_number: Process number to check
            
        Returns:
            Process status information
        """
        query = """
        MATCH (process:Process {number: $processNumber})
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        WITH process, COLLECT(stage) as allStages, COLLECT(stage)[0] as latestStage
        
        RETURN 
          process.number as processNumber,
          CASE 
            WHEN latestStage IS NULL THEN 'unknown'
            WHEN latestStage.type IN ['PUBLICATION', 'WITHDRAWAL'] THEN 'finished'
            ELSE 'active'
          END as status,
          latestStage.stageName as currentStage,
          latestStage.date as stageDate,
          [s in allStages | {
            stageName: s.stageName,
            date: s.date,
            number: s.number,
            type: s.type,
            decision: s.decision,
            comment: s.comment
          }] as allStages
        """
        
        results = neo4j_client.execute_read_query(query, {"processNumber": process_number})
        
        if not results:
            return None
        
        return ProcessStatus(**results[0])
    
    def find_person_by_name(self, name: str) -> List[Person]:
        """
        Find MPs by name using fulltext search
        
        Args:
            name: Name to search for
            
        Returns:
            List of matching persons
        """
        query = """
        CALL db.index.fulltext.queryNodes("person_names", $name) 
        YIELD node, score
        WHERE node.club IS NOT NULL
        
        RETURN 
          node.id as id,
          node.firstLastName as name,
          node.club as club,
          node.role as role,
          node.active as active,
          score
        ORDER BY score DESC
        LIMIT 10
        """
        
        results = neo4j_client.execute_read_query(query, {"name": name})
        return [Person(**r) for r in results]
    
    def get_person_activity(self, person_id: int) -> Optional[PersonActivity]:
        """
        Get legislative activity for an MP
        
        Args:
            person_id: Person ID
            
        Returns:
            Person's legislative activity
        """
        # Get person info
        person_query = """
        MATCH (p:Person {id: $personId})
        RETURN 
          p.id as id,
          p.firstLastName as name,
          p.club as club,
          p.role as role,
          p.active as active
        """
        
        person_results = neo4j_client.execute_read_query(person_query, {"personId": person_id})
        
        if not person_results:
            return None
        
        person = Person(**person_results[0])
        
        # Get authored prints
        authored_query = """
        MATCH (p:Person {id: $personId})-[:AUTHORED]->(print:Print)
        OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
        
        WITH print, COLLECT(DISTINCT topic.name) as topics
        
        RETURN 
          print.number as number,
          print.title as title,
          print.summary as summary,
          print.documentDate as documentDate,
          topics
        ORDER BY print.documentDate DESC
        LIMIT 10
        """
        
        authored_results = neo4j_client.execute_read_query(authored_query, {"personId": person_id})
        authored_prints = [PrintShort(**r) for r in authored_results]
        
        # Get subject prints (prints about this person)
        subject_query = """
        MATCH (p:Person {id: $personId})-[:SUBJECT]->(print:Print)
        OPTIONAL MATCH (print)-[:REFERS_TO]->(topic:Topic)
        
        WITH print, COLLECT(DISTINCT topic.name) as topics
        
        RETURN 
          print.number as number,
          print.title as title,
          print.summary as summary,
          print.documentDate as documentDate,
          topics
        ORDER BY print.documentDate DESC
        LIMIT 10
        """
        
        subject_results = neo4j_client.execute_read_query(subject_query, {"personId": person_id})
        subject_prints = [PrintShort(**r) for r in subject_results]
        
        # Get speech count
        speech_query = """
        MATCH (p:Person {id: $personId})-[:SAID]->()
        RETURN count(*) as count
        """
        
        speech_results = neo4j_client.execute_read_query(speech_query, {"personId": person_id})
        speech_count = speech_results[0]["count"] if speech_results else 0
        
        # Get committees
        committee_query = """
        MATCH (p:Person {id: $personId})-[r:BELONGS_TO]->(c:Committee)
        RETURN c.name as name
        """
        
        committee_results = neo4j_client.execute_read_query(committee_query, {"personId": person_id})
        committees = [r["name"] for r in committee_results]
        
        return PersonActivity(
            person=person,
            authoredPrints=authored_prints,
            subjectPrints=subject_prints,
            speechCount=speech_count,
            committees=committees
        )
    
    def get_club_statistics(self, club_name: str) -> Optional[ClubStatistics]:
        """
        Get comprehensive statistics about a parliamentary club (party)
        
        Args:
            club_name: Club name to get statistics for
            
        Returns:
            Club statistics or None if not found
        """
        query = """
        MATCH (club:Club {name: $clubName})
        
        // Count members
        OPTIONAL MATCH (member:Person {club: $clubName})
        WITH club, member
        WITH club,
             count(DISTINCT member) as memberCount,
             sum(CASE WHEN member.active = true THEN 1 ELSE 0 END) as activeMembers
        
        // Count authored prints
        OPTIONAL MATCH (author:Person {club: $clubName})-[:AUTHORED]->(print:Print)
        WITH club, memberCount, activeMembers, print
        WITH club, memberCount, activeMembers,
             count(DISTINCT print) as authoredPrints
        
        // Separate active and finished authored prints
        OPTIONAL MATCH (author:Person {club: $clubName})-[:AUTHORED]->(print2:Print)
        OPTIONAL MATCH (print2)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH club, memberCount, activeMembers, authoredPrints, print2, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        WITH club, memberCount, activeMembers, authoredPrints, print2, process,
             COLLECT(stage)[0] as latestStage
        
        WITH club, memberCount, activeMembers, authoredPrints,
             sum(CASE 
               WHEN process IS NULL 
                    OR latestStage IS NULL 
                    OR latestStage.type IS NULL
                    OR NOT (latestStage.type IN ['PUBLICATION', 'WITHDRAWAL'])
               THEN 1 
               ELSE 0
             END) as activePrints,
             sum(CASE 
               WHEN latestStage.type IN ['PUBLICATION', 'WITHDRAWAL']
               THEN 1 
               ELSE 0
             END) as finishedPrints
        
        // Count votes and speeches
        OPTIONAL MATCH (voter:Person {club: $clubName})-[vote:VOTED]->()
        OPTIONAL MATCH (speaker:Person {club: $clubName})-[speech:SAID]->()
        
        WITH club, memberCount, activeMembers, authoredPrints, activePrints, 
             finishedPrints,
             count(DISTINCT vote) as totalVotes,
             count(DISTINCT speech) as speechCount
        
        // Count committee positions
        OPTIONAL MATCH (member:Person {club: $clubName})-[:BELONGS_TO]->(committee:Committee)
        WITH club, memberCount, activeMembers, authoredPrints, activePrints,
             finishedPrints, totalVotes, speechCount,
             count(DISTINCT committee) as committeePositions
        
        RETURN 
          club.name as name,
          memberCount,
          activeMembers,
          authoredPrints,
          activePrints,
          finishedPrints,
          totalVotes,
          speechCount,
          committeePositions
        """
        
        results = neo4j_client.execute_read_query(query, {"clubName": club_name})
        
        if not results:
            return None
        
        return ClubStatistics(**results[0])
    
    def get_node_neighbors(
        self, 
        node_type: str, 
        node_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all neighboring nodes for a given node (generic exploration)
        
        Args:
            node_type: Type of node (e.g., 'Person', 'Print', 'Topic', 'Process', 'Club')
            node_id: Node identifier (depends on type - id, number, name, etc.)
            limit: Maximum neighbors per relationship type
            
        Returns:
            Dictionary with neighbor information grouped by relationship type
        """
        # Build query based on node type
        if node_type == 'Person':
            match_clause = "MATCH (n:Person {id: $nodeId})"
        elif node_type == 'Print':
            match_clause = "MATCH (n:Print {number: $nodeId})"
        elif node_type == 'Topic':
            match_clause = "MATCH (n:Topic {name: $nodeId})"
        elif node_type == 'Process':
            match_clause = "MATCH (n:Process {number: $nodeId})"
        elif node_type == 'Club':
            match_clause = "MATCH (n:Club {name: $nodeId})"
        elif node_type == 'Committee':
            match_clause = "MATCH (n:Committee {code: $nodeId})"
        else:
            # Generic fallback
            match_clause = f"MATCH (n:{node_type}) WHERE id(n) = toInteger($nodeId)"
        
        query = f"""
        {match_clause}
        
        // Get all relationships and neighbors
        OPTIONAL MATCH (n)-[r]-(neighbor)
        
        WITH n, type(r) as relType, labels(neighbor)[0] as neighborType, 
             COLLECT(DISTINCT neighbor) as neighbors
        WHERE relType IS NOT NULL
        
        // Return grouped by relationship type
        RETURN 
          relType,
          neighborType,
          [nb in neighbors[0..$limit] | 
            CASE labels(nb)[0]
              WHEN 'Person' THEN {{
                id: nb.id,
                name: nb.firstLastName,
                club: nb.club
              }}
              WHEN 'Print' THEN {{
                number: nb.number,
                title: nb.title
              }}
              WHEN 'Topic' THEN {{
                name: nb.name,
                description: nb.description
              }}
              WHEN 'Process' THEN {{
                number: nb.number,
                title: nb.title
              }}
              WHEN 'Club' THEN {{
                name: nb.name
              }}
              WHEN 'Committee' THEN {{
                code: nb.code,
                name: nb.name
              }}
              WHEN 'Statement' THEN {{
                speaker: nb.statement_speaker,
                topic: nb.statement_official_topic
              }}
              WHEN 'Stage' THEN {{
                stageName: nb.stageName,
                date: nb.date,
                type: nb.type
              }}
              ELSE {{
                info: 'Node type: ' + labels(nb)[0]
              }}
            END
          ] as neighborData,
          size(neighbors) as totalCount
        ORDER BY totalCount DESC
        """
        
        try:
            results = neo4j_client.execute_read_query(query, {
                "nodeId": node_id,
                "limit": limit
            })
            
            # Group results by relationship type
            grouped = {}
            for r in results:
                rel_type = r['relType']
                if rel_type not in grouped:
                    grouped[rel_type] = {
                        'neighborType': r['neighborType'],
                        'totalCount': r['totalCount'],
                        'neighbors': r['neighborData']
                    }
            
            return grouped
        except Exception as e:
            logger.error(f"Error getting node neighbors: {e}")
            return {}
    
    def list_clubs(self) -> List[Club]:
        """
        Get list of all parliamentary clubs (parties)
        
        Returns:
            List of all clubs with their member counts
        """
        query = """
        // Get all unique clubs
        MATCH (person:Person)
        WHERE person.club IS NOT NULL
        
        WITH DISTINCT person.club as clubName
        
        // Count total members per club
        OPTIONAL MATCH (member:Person {club: clubName})
        WITH clubName, count(DISTINCT member) as memberCount
        
        // Count active members per club
        OPTIONAL MATCH (activeMember:Person {club: clubName, active: true})
        WITH clubName, memberCount, count(DISTINCT activeMember) as activeMembers
        
        RETURN 
          clubName as name,
          memberCount,
          activeMembers
        ORDER BY memberCount DESC
        """
        
        results = neo4j_client.execute_read_query(query, {})
        return [Club(**r) for r in results]


# Global query service instance
query_service = QueryService()
