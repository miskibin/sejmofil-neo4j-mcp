import os
import json
from neo4j import GraphDatabase
import dotenv
from loguru import logger

# Configure loguru
logger.remove()
logger.add(lambda msg: print(msg, end=""), format="{message}", level="INFO")

# Load .env from parent directory
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Neo4jSchemaFetcher:
    def __init__(self, uri, user, password, database="neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        logger.info(f"Connected to database: {database}")

    def close(self):
        self.driver.close()
        logger.info("Connection closed")

    def _serialize(self, obj):
        """Convert non-serializable objects to JSON-compatible types"""
        if hasattr(obj, '__dict__'):
            return str(obj)
        return str(obj)

    def fetch_schema(self):
        """Fetch complete schema using Neo4j 5.x SHOW commands"""
        logger.info("Fetching database schema...")
        with self.driver.session(database=self.database) as session:
            logger.debug("Fetching labels...")
            labels = [record["label"] for record in session.run("CALL db.labels()")]
            
            logger.debug("Fetching relationship types...")
            rel_types = [record["relationshipType"] for record in session.run("CALL db.relationshipTypes()")]
            
            logger.debug("Fetching indexes...")
            indexes = [{k: v for k, v in dict(record).items() if k not in ["state", "lastRead", "readCount"]} 
                      for record in session.run("SHOW INDEXES")]
            
            logger.debug("Fetching constraints...")
            constraints = [dict(record) for record in session.run("SHOW CONSTRAINTS")]

        logger.info(f"Found {len(labels)} labels, {len(rel_types)} relationship types, {len(indexes)} indexes, {len(constraints)} constraints")
        
        return {
            "labels": labels,
            "relationshipTypes": rel_types,
            "indexes": indexes,
            "constraints": constraints,
        }


if __name__ == "__main__":
    try:
        fetcher = Neo4jSchemaFetcher(
            uri=os.getenv("NEO4J_HOST"),
            user=os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD"),
        )

        schema = fetcher.fetch_schema()
        fetcher.close()

        # Save to JSON file
        output_file = os.path.join(os.path.dirname(__file__), "..", "db_schema.json")
        logger.info(f"Saving schema to {output_file}...")
        
        with open(output_file, "w") as f:
            json.dump(schema, f, indent=2, default=str)

        logger.success(f"Schema saved to {output_file}")
        logger.info(json.dumps(schema, indent=2, default=str))
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
