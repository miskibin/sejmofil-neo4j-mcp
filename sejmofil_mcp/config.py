"""Configuration management for Sejmofil MCP Server"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Neo4j configuration
    NEO4J_HOST: str = "bolt+s://neo.msulawiak.pl:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # OpenAI configuration for embeddings
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDINGS_MODEL: str = "text-embedding-3-small"
    
    # Query limits
    DEFAULT_LIMIT: int = 10
    MAX_LIMIT: int = 50
    
    # Similarity thresholds
    VECTOR_SIMILARITY_THRESHOLD: float = 0.5
    TOPIC_SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
