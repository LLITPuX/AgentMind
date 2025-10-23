"""
Embedding utilities for vector similarity and deduplication.

Uses OpenAI embeddings for semantic similarity comparison.
"""

from typing import List, Tuple, Optional
import os
import logging
from langchain_openai import OpenAIEmbeddings
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Manages embeddings generation and similarity calculations.
    
    Uses OpenAI's text-embedding-3-small model for efficient embeddings.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        """
        Initialize EmbeddingManager.
        
        Args:
            api_key: OpenAI API key (default: from environment)
            model: Embedding model to use
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=self.api_key,
            model=self.model
        )
        
        logger.info(f"EmbeddingManager initialized with model: {model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.embeddings.embed_query(text)
            logger.debug(f"Generated embedding for text: '{text[:50]}...'")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.embeddings.embed_documents(texts)
            logger.debug(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity formula: (A · B) / (||A|| * ||B||)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        
        # Ensure result is in [0, 1] range
        similarity = max(0.0, min(1.0, float(similarity)))
        
        return similarity
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        threshold: float = 0.85
    ) -> Tuple[int, float]:
        """
        Find the most similar embedding from candidates.
        
        Args:
            query_embedding: Embedding to compare against
            candidate_embeddings: List of candidate embeddings
            threshold: Minimum similarity threshold
        
        Returns:
            Tuple of (index, similarity) for the most similar candidate,
            or (-1, 0.0) if no candidate exceeds threshold
        """
        if not candidate_embeddings:
            return -1, 0.0
        
        similarities = [
            self.cosine_similarity(query_embedding, candidate)
            for candidate in candidate_embeddings
        ]
        
        max_similarity = max(similarities)
        max_index = similarities.index(max_similarity)
        
        if max_similarity >= threshold:
            logger.debug(f"Found similar embedding at index {max_index} with similarity {max_similarity:.3f}")
            return max_index, max_similarity
        
        logger.debug(f"No similar embedding found (max similarity: {max_similarity:.3f} < threshold: {threshold})")
        return -1, 0.0


# Singleton instance for global use
_embedding_manager: Optional[EmbeddingManager] = None


def get_embedding_manager(force_new: bool = False) -> EmbeddingManager:
    """
    Get or create the global EmbeddingManager instance.
    
    Args:
        force_new: If True, create a new instance even if one exists
    
    Returns:
        Singleton EmbeddingManager instance
    """
    global _embedding_manager
    
    if _embedding_manager is None or force_new:
        _embedding_manager = EmbeddingManager()
    
    return _embedding_manager


def reset_embedding_manager() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _embedding_manager
    _embedding_manager = None

