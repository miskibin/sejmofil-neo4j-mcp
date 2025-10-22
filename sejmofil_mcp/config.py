"""Configuration management for Sejmofil MCP Server"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Neo4j configuration
    NEO4J_HOST: str = "bolt+s://neo.msulawiak.pl:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str
    
    # OpenAI configuration for embeddings
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDINGS_MODEL: str = "text-embedding-3-small"
    
    # API Key Authorization
    # Comma-separated list of valid API keys for authorization
    # If not set, authorization is disabled
    API_KEYS: Optional[str] = None
    
    # Query limits
    DEFAULT_LIMIT: int = 10
    MAX_LIMIT: int = 50
    
    # Similarity thresholds
    VECTOR_SIMILARITY_THRESHOLD: float = 0.5
    TOPIC_SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def get_valid_api_keys(self) -> List[str]:
        """Get list of valid API keys from comma-separated string"""
        if not self.API_KEYS:
            return []
        return [key.strip() for key in self.API_KEYS.split(',') if key.strip()]
    
    def is_api_key_valid(self, api_key: str) -> bool:
        """Check if an API key is valid"""
        valid_keys = self.get_valid_api_keys()
        if not valid_keys:
            # If no API keys configured, allow access
            return True
        return api_key in valid_keys


settings = Settings()
