"""Embeddings generation using OpenAI API"""

from typing import List, Optional
from openai import OpenAI
from loguru import logger
from config import settings


class EmbeddingsService:
    """Service for generating text embeddings using OpenAI"""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"Embeddings service initialized with model: {settings.EMBEDDINGS_MODEL}")
        else:
            logger.warning("OPENAI_API_KEY not set, embeddings functionality disabled")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized. Set OPENAI_API_KEY environment variable.")
        
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            response = self.client.embeddings.create(
                model=settings.EMBEDDINGS_MODEL,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if embeddings service is available"""
        return self.client is not None


# Global embeddings service instance
embeddings_service = EmbeddingsService()
