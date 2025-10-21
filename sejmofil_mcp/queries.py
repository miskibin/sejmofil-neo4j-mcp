"""Cypher queries for Neo4j database"""

from typing import List, Dict, Any, Optional
from loguru import logger
from neo4j_client import neo4j_client
from embeddings import embeddings_service
from models import (
    PrintShort, PrintDetail, Comment, Person, PersonActivity,
    Topic, VotingResult, ProcessStatus, ProcessStage, SearchResult
)
from config import settings


class QueryService:
    """Service for executing Neo4j queries"""
    
    def search_active_prints_by_topic(
        self, 
        topic: str, 
        limit: int = 10
    ) -> List[PrintShort]:
        """
        Search for active (currently processed) prints on a topic using semantic search
        
        Args:
            topic: Topic to search for (will be converted to embedding)
            limit: Maximum number of results
            
        Returns:
            List of active prints matching the topic
        """
        if not embeddings_service.is_available():
            logger.warning("Embeddings service not available, falling back to fulltext search")
            return self._search_prints_fulltext(topic, limit, active_only=True)
        
        # Generate embedding for the topic
        embedding = embeddings_service.generate_embedding(topic)
        
        query = """
        // Vector search on prints
        CALL db.index.vector.queryNodes('printEmbeddingIndex', $limit * 2, $embedding)
        YIELD node as print, score
        WHERE print.summary IS NOT NULL
        
        // Get process and stages - use correct relationship
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH print, score, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        // Get latest stage per print
        WITH print, score, process, COLLECT(stage)[0] as latestStage
        
        // Filter active only - stages with terminal names or no process at all
        WHERE process IS NULL
           OR latestStage IS NULL 
           OR (latestStage.stageName IS NOT NULL 
               AND NOT latestStage.stageName IN [
                 'Publikacja w Dzienniku Ustaw',
                 'Odrzucenie projektu ustawy',
                 'Wycofanie projektu'
               ])
        
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
        active_only: bool = False
    ) -> List[PrintShort]:
        """Fallback fulltext search for prints"""
        
        query = """
        CALL db.index.fulltext.queryNodes("print_content", $query) 
        YIELD node as print, score
        WHERE print.summary IS NOT NULL
        """
        
        if active_only:
            query += """
            // Get process status - use OPTIONAL MATCH for prints without process
            OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
            OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
            
            WITH print, score, process, stage
            ORDER BY stage.date DESC, stage.number DESC
            
            WITH print, score, process, COLLECT(stage)[0] as latestStage
            WHERE process IS NULL
               OR latestStage IS NULL 
               OR (latestStage.stageName IS NOT NULL 
                   AND NOT latestStage.stageName IN [
                     'Publikacja w Dzienniku Ustaw',
                     'Odrzucenie projektu ustawy',
                     'Wycofanie projektu'
                   ])
            """
        else:
            query += """
            WITH print, score, null as latestStage
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
            WHEN latestStage.stageName IN [
              'Publikacja w Dzienniku Ustaw', 
              'Odrzucenie projektu ustawy',
              'Wycofanie projektu'
            ] THEN 'finished'
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
    
    def get_similar_topics(
        self, 
        topic_name: str, 
        limit: int = 5
    ) -> List[Topic]:
        """
        Find topics semantically similar to a given topic
        
        Args:
            topic_name: Topic name to find similar topics for
            limit: Maximum number of results
            
        Returns:
            List of similar topics
        """
        query = """
        MATCH (sourceTopic:Topic {name: $topicName})
        WHERE sourceTopic.embedding IS NOT NULL
        
        WITH sourceTopic
        MATCH (otherTopic:Topic)
        WHERE otherTopic <> sourceTopic 
          AND otherTopic.embedding IS NOT NULL
        
        WITH otherTopic, sourceTopic,
             gds.similarity.cosine(sourceTopic.embedding, otherTopic.embedding) as similarity
        WHERE similarity > $threshold
        
        // Get print count for each topic
        OPTIONAL MATCH (otherTopic)<-[:REFERS_TO]-(print:Print)
        WITH otherTopic, similarity, count(print) as printCount
        
        RETURN 
          otherTopic.name as name,
          otherTopic.description as description,
          printCount,
          similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        results = neo4j_client.execute_read_query(query, {
            "topicName": topic_name,
            "threshold": settings.TOPIC_SIMILARITY_THRESHOLD,
            "limit": limit
        })
        
        return [Topic(**r) for r in results]
    
    def search_all(self, query_text: str, limit: int = 20) -> Dict[str, List[SearchResult]]:
        """
        Search across prints, persons, and topics
        
        Args:
            query_text: Search query
            limit: Results per category
            
        Returns:
            Dictionary with results by type
        """
        # Search prints
        print_results = self._search_prints_fulltext(query_text, limit)
        
        # Search persons
        person_results = self.find_person_by_name(query_text)
        
        # Convert to generic search results
        return {
            "prints": [
                SearchResult(
                    type="print",
                    id=p.number,
                    title=p.title,
                    description=p.summary,
                    relevance=p.score
                ) for p in print_results
            ],
            "persons": [
                SearchResult(
                    type="person",
                    id=str(p.id) if p.id else p.name,
                    title=p.name,
                    description=f"{p.club} - {p.role}" if p.club and p.role else None,
                    relevance=None
                ) for p in person_results
            ]
        }
    
    def get_topic_statistics(self, topic_name: str) -> Dict[str, Any]:
        """
        Get statistics about a topic
        
        Args:
            topic_name: Topic name
            
        Returns:
            Topic statistics
        """
        query = """
        MATCH (topic:Topic {name: $topicName})
        OPTIONAL MATCH (topic)<-[:REFERS_TO]-(print:Print)
        
        WITH topic, print
        OPTIONAL MATCH (print)-[:IS_SOURCE_OF]->(process:Process)
        OPTIONAL MATCH (process)-[:HAS]->(stage:Stage)
        
        WITH topic, print, process, stage
        ORDER BY stage.date DESC, stage.number DESC
        
        WITH topic, print, process, COLLECT(stage)[0] as latestStage
        
        // Separate active and finished prints
        WITH topic,
             count(DISTINCT print) as totalPrints,
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
             END) as activePrints,
             sum(CASE 
               WHEN latestStage.stageName IN [
                 'Publikacja w Dzienniku Ustaw',
                 'Odrzucenie projektu ustawy',
                 'Wycofanie projektu'
               ]
               THEN 1 
               ELSE 0
             END) as finishedPrints
        
        RETURN 
          topic.name as name,
          topic.description as description,
          totalPrints,
          activePrints,
          finishedPrints
        """
        
        results = neo4j_client.execute_read_query(query, {"topicName": topic_name})
        
        if not results:
            return {}
        
        return results[0]


# Global query service instance
query_service = QueryService()
