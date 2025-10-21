"""Neo4j database client"""

from typing import Any, Dict, List, Optional
from neo4j import GraphDatabase, Driver, Session
from loguru import logger
from config import settings


class Neo4jClient:
    """Neo4j database client with connection management"""
    
    def __init__(self):
        self.driver: Optional[Driver] = None
        
    def connect(self) -> None:
        """Establish connection to Neo4j database"""
        try:
            logger.info(f"Connecting to Neo4j at {settings.NEO4J_HOST}")
            self.driver = GraphDatabase.driver(
                settings.NEO4J_HOST,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dictionaries
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not connected")
        
        parameters = parameters or {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                records = [dict(record) for record in result]
                logger.debug(f"Query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise
    
    def execute_read_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a read query in a read transaction
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        if not self.driver:
            raise RuntimeError("Neo4j driver not connected")
        
        parameters = parameters or {}
        
        def _execute_read(tx):
            result = tx.run(query, parameters)
            return [dict(record) for record in result]
        
        try:
            with self.driver.session() as session:
                records = session.execute_read(_execute_read)
                logger.debug(f"Read query returned {len(records)} records")
                return records
        except Exception as e:
            logger.error(f"Read query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise


# Global client instance
neo4j_client = Neo4jClient()
