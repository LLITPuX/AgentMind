"""
Pydantic models for LLM structured extraction.

These models define the schema for extracting entities and relationships
from observations using LLM with structured output.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from .schema import GraphType


class ExtractedEntity(BaseModel):
    """
    Entity extracted from observations by LLM.
    
    Represents a conceptual entity that should be stored in the knowledge graph.
    """
    label: str = Field(
        ...,
        description="Type of entity (e.g., Person, Organization, Concept, Action)"
    )
    name: str = Field(
        ...,
        description="Name or identifier of the entity"
    )
    graph_type: GraphType = Field(
        ...,
        description="Internal (agent self-concept) or External (world knowledge)"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties of the entity"
    )
    valid_from: Optional[datetime] = Field(
        default=None,
        description="When this entity became valid"
    )
    valid_until: Optional[datetime] = Field(
        default=None,
        description="When this entity ceased to be valid"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "label": "Person",
                    "name": "Alice",
                    "graph_type": "internal",
                    "properties": {"role": "user"},
                    "valid_from": "2025-01-01T00:00:00",
                    "valid_until": None
                }
            ]
        }
    }


class ExtractedRelation(BaseModel):
    """
    Relationship between entities extracted by LLM.
    
    Represents a conceptual edge that should be stored in the knowledge graph.
    """
    edge_type: str = Field(
        ...,
        description="Type of relationship (e.g., WORKS_AT, LIKES, KNOWS)"
    )
    from_entity_name: str = Field(
        ...,
        description="Name of the source entity"
    )
    to_entity_name: str = Field(
        ...,
        description="Name of the target entity"
    )
    graph_type: GraphType = Field(
        ...,
        description="Internal or External graph space"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional properties of the relationship"
    )
    valid_from: Optional[datetime] = Field(
        default=None,
        description="When this relationship became valid"
    )
    valid_until: Optional[datetime] = Field(
        default=None,
        description="When this relationship ceased to be valid"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edge_type": "LIKES",
                    "from_entity_name": "Alice",
                    "to_entity_name": "Python",
                    "graph_type": "internal",
                    "properties": {"confidence": 0.9}
                }
            ]
        }
    }


class ExtractionResult(BaseModel):
    """
    Complete result of entity extraction from observations.
    
    Contains all entities and relationships extracted by LLM.
    """
    entities: List[ExtractedEntity] = Field(
        default_factory=list,
        description="List of extracted entities"
    )
    relations: List[ExtractedRelation] = Field(
        default_factory=list,
        description="List of extracted relationships"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entities": [
                        {"label": "Person", "name": "Alice", "graph_type": "internal"},
                        {"label": "Language", "name": "Python", "graph_type": "external"}
                    ],
                    "relations": [
                        {
                            "edge_type": "LIKES",
                            "from_entity_name": "Alice",
                            "to_entity_name": "Python",
                            "graph_type": "internal"
                        }
                    ]
                }
            ]
        }
    }

