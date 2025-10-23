"""
Schema definitions for AgentMind Memory System

This module defines the data models for the reflexive memory architecture,
including bitemporal tracking, Statement-based knowledge representation,
and logical separation of Internal/External graphs.

Based on: Reflexive_Memory_Architecture.md
"""

from datetime import datetime
from typing import Optional, Dict, Any, Literal
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self


class GraphType(str, Enum):
    """
    Logical separation of graph spaces.
    
    - INTERNAL: Agent's self-concept, user profile, policies
    - EXTERNAL: Objective world knowledge with source attribution
    """
    INTERNAL = "internal"
    EXTERNAL = "external"


class SourceType(str, Enum):
    """Type of information source"""
    USER = "user"
    AGENT_INFERENCE = "agent_inference"
    SYSTEM_CONFIG = "system_config"
    EXPLICIT_POLICY = "explicit_policy"
    EXTERNAL_API = "external_api"
    DOCUMENT = "document"
    OTHER = "other"


class Source(BaseModel):
    """
    Attribution for a piece of information.
    
    Tracks who/what provided the information and its reliability.
    """
    name: str = Field(..., description="Name/identifier of the source")
    type: SourceType = Field(..., description="Type of source")
    reliability_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Reliability score [0.0-1.0]"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source metadata"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "User_001",
                    "type": "user",
                    "reliability_score": 1.0,
                    "metadata": {"session_id": "abc123"}
                }
            ]
        }
    }


class BiTemporalMixin(BaseModel):
    """
    Bitemporal tracking for all memory entities.
    
    - Valid Time: When the fact was true in the real world
    - Transaction Time: When we learned about the fact
    
    This allows us to:
    1. Query "what did we know at time T?"
    2. Query "what was true at time T?"
    3. Handle corrections and conflicting information
    """
    valid_from: datetime = Field(
        default_factory=datetime.now,
        description="When this fact became valid in reality"
    )
    valid_until: datetime = Field(
        default=datetime(9999, 12, 31, 23, 59, 59),
        description="When this fact ceased to be valid (far future = ongoing)"
    )
    tx_time_from: datetime = Field(
        default_factory=datetime.now,
        description="When we recorded this fact"
    )
    tx_time_to: Optional[datetime] = Field(
        default=None,
        description="When this record was superseded/expired (None = current)"
    )
    
    @field_validator('valid_until')
    @classmethod
    def valid_until_must_be_after_valid_from(cls, v: datetime, info) -> datetime:
        """Ensure valid_until is after valid_from"""
        if 'valid_from' in info.data and v < info.data['valid_from']:
            raise ValueError('valid_until must be after valid_from')
        return v
    
    @field_validator('tx_time_to')
    @classmethod
    def tx_time_to_must_be_after_tx_time_from(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure tx_time_to is after tx_time_from if set"""
        if v is not None and 'tx_time_from' in info.data and v < info.data['tx_time_from']:
            raise ValueError('tx_time_to must be after tx_time_from')
        return v


class ConceptualNode(BiTemporalMixin):
    """
    A conceptual entity in the knowledge graph.
    
    Represents things like Person, Organization, Concept, Action, etc.
    Can belong to either Internal or External graph space.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier"
    )
    label: str = Field(
        ...,
        description="Node label/type (e.g., Person, Organization, Action)"
    )
    name: str = Field(
        ...,
        description="Human-readable name of the entity"
    )
    graph_type: GraphType = Field(
        ...,
        description="Which graph space this belongs to"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties specific to this entity"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "label": "Person",
                    "name": "Elon Musk",
                    "graph_type": "external",
                    "properties": {"occupation": "CEO"}
                }
            ]
        }
    }


class ConceptualEdge(BiTemporalMixin):
    """
    A relationship between conceptual entities.
    
    Represents relationships like CEO_OF, KNOWS, LOCATED_IN, etc.
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier"
    )
    edge_type: str = Field(
        ...,
        description="Type of relationship (e.g., CEO_OF, KNOWS)"
    )
    from_node_id: str = Field(
        ...,
        description="Source node ID"
    )
    to_node_id: str = Field(
        ...,
        description="Target node ID"
    )
    graph_type: GraphType = Field(
        ...,
        description="Which graph space this belongs to"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties of this relationship"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edge_type": "CEO_OF",
                    "from_node_id": "person-123",
                    "to_node_id": "company-456",
                    "graph_type": "external"
                }
            ]
        }
    }


class Statement(BiTemporalMixin):
    """
    A claim/assertion about a conceptual entity (node or edge).
    
    This is the core of our "multi-source truth" model:
    - Instead of storing facts directly, we store CLAIMS about facts
    - Each claim has attribution (Source)
    - Multiple conflicting claims can coexist
    - The agent can reason about which to trust
    
    Example: Instead of edge [Elon] -CEO_OF-> [Tesla],
    we have ConceptualEdge(CEO_OF) + Statement(source=BoardOfDirectors, valid_until=2025-10-23)
                                   + Statement(source=Lawyer, valid_until=9999-12-31)
    """
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier"
    )
    asserts_about_conceptual_id: str = Field(
        ...,
        description="ID of the ConceptualNode or ConceptualEdge this statement is about"
    )
    source: Source = Field(
        ...,
        description="Who/what made this claim"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="The actual content of the claim"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in this statement [0.0-1.0]"
    )
    
    @field_validator('confidence')
    @classmethod
    def confidence_must_be_valid(cls, v: float) -> float:
        """Ensure confidence is in valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('confidence must be between 0.0 and 1.0')
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "asserts_about_conceptual_id": "edge-ceo-123",
                    "source": {
                        "name": "Board of Directors",
                        "type": "external_api",
                        "reliability_score": 0.9
                    },
                    "attributes": {
                        "status": "terminated",
                        "reason": "board_decision"
                    },
                    "confidence": 0.95
                }
            ]
        }
    }


# Convenience type aliases
InternalNode = ConceptualNode
ExternalNode = ConceptualNode
InternalEdge = ConceptualEdge
ExternalEdge = ConceptualEdge

