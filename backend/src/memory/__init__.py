"""
Memory management module for AgentMind

This module handles both short-term memory (STM) and long-term memory (LTM)
using FalkorDB as the underlying graph database.
"""

from .manager import MemoryManager
from .stm import ShortTermMemoryBuffer, Observation
from .schema import (
    GraphType,
    SourceType,
    Source,
    BiTemporalMixin,
    ConceptualNode,
    ConceptualEdge,
    Statement,
)
from .consolidation import ConsolidationGraph
from .extraction_models import ExtractedEntity, ExtractedRelation, ExtractionResult
from .embeddings import EmbeddingManager, get_embedding_manager

__all__ = [
    "MemoryManager",
    "ShortTermMemoryBuffer",
    "Observation",
    "GraphType",
    "SourceType",
    "Source",
    "BiTemporalMixin",
    "ConceptualNode",
    "ConceptualEdge",
    "Statement",
    "ConsolidationGraph",
    "ExtractedEntity",
    "ExtractedRelation",
    "ExtractionResult",
    "EmbeddingManager",
    "get_embedding_manager",
]

