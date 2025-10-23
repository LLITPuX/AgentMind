"""
Unit tests for extraction models.

Tests Pydantic models used for LLM structured output.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.memory.extraction_models import ExtractedEntity, ExtractedRelation, ExtractionResult
from src.memory.schema import GraphType


@pytest.mark.unit
class TestExtractedEntity:
    """Tests for ExtractedEntity model"""
    
    def test_can_create_basic_entity(self):
        """Test creating a basic entity"""
        entity = ExtractedEntity(
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL
        )
        
        assert entity.label == "Person"
        assert entity.name == "Alice"
        assert entity.graph_type == GraphType.INTERNAL
        assert entity.properties == {}
        assert entity.valid_from is None
        assert entity.valid_until is None
    
    def test_can_create_entity_with_properties(self):
        """Test creating entity with properties"""
        entity = ExtractedEntity(
            label="Person",
            name="Bob",
            graph_type=GraphType.EXTERNAL,
            properties={"age": 30, "occupation": "Engineer"}
        )
        
        assert entity.properties["age"] == 30
        assert entity.properties["occupation"] == "Engineer"
    
    def test_can_create_entity_with_temporal_info(self):
        """Test creating entity with temporal information"""
        valid_from = datetime(2025, 1, 1)
        valid_until = datetime(2025, 12, 31)
        
        entity = ExtractedEntity(
            label="Project",
            name="Project Alpha",
            graph_type=GraphType.EXTERNAL,
            valid_from=valid_from,
            valid_until=valid_until
        )
        
        assert entity.valid_from == valid_from
        assert entity.valid_until == valid_until
    
    def test_entity_can_be_serialized(self):
        """Test entity serialization"""
        entity = ExtractedEntity(
            label="Organization",
            name="Google",
            graph_type=GraphType.EXTERNAL,
            properties={"founded": 1998}
        )
        
        data = entity.model_dump()
        
        assert data["label"] == "Organization"
        assert data["name"] == "Google"
        assert data["graph_type"] == "external"
        assert data["properties"]["founded"] == 1998


@pytest.mark.unit
class TestExtractedRelation:
    """Tests for ExtractedRelation model"""
    
    def test_can_create_basic_relation(self):
        """Test creating a basic relation"""
        relation = ExtractedRelation(
            edge_type="LIKES",
            from_entity_name="Alice",
            to_entity_name="Python",
            graph_type=GraphType.INTERNAL
        )
        
        assert relation.edge_type == "LIKES"
        assert relation.from_entity_name == "Alice"
        assert relation.to_entity_name == "Python"
        assert relation.graph_type == GraphType.INTERNAL
        assert relation.properties == {}
    
    def test_can_create_relation_with_properties(self):
        """Test creating relation with properties"""
        relation = ExtractedRelation(
            edge_type="WORKS_AT",
            from_entity_name="Bob",
            to_entity_name="Google",
            graph_type=GraphType.EXTERNAL,
            properties={"since": "2020", "position": "Engineer"}
        )
        
        assert relation.properties["since"] == "2020"
        assert relation.properties["position"] == "Engineer"
    
    def test_relation_can_be_serialized(self):
        """Test relation serialization"""
        relation = ExtractedRelation(
            edge_type="KNOWS",
            from_entity_name="Alice",
            to_entity_name="Bob",
            graph_type=GraphType.EXTERNAL
        )
        
        data = relation.model_dump()
        
        assert data["edge_type"] == "KNOWS"
        assert data["from_entity_name"] == "Alice"
        assert data["to_entity_name"] == "Bob"
        assert data["graph_type"] == "external"


@pytest.mark.unit
class TestExtractionResult:
    """Tests for ExtractionResult model"""
    
    def test_can_create_empty_result(self):
        """Test creating empty extraction result"""
        result = ExtractionResult()
        
        assert result.entities == []
        assert result.relations == []
    
    def test_can_create_result_with_entities_and_relations(self):
        """Test creating result with entities and relations"""
        entities = [
            ExtractedEntity(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            ),
            ExtractedEntity(
                label="Language",
                name="Python",
                graph_type=GraphType.EXTERNAL
            )
        ]
        
        relations = [
            ExtractedRelation(
                edge_type="LIKES",
                from_entity_name="Alice",
                to_entity_name="Python",
                graph_type=GraphType.INTERNAL
            )
        ]
        
        result = ExtractionResult(
            entities=entities,
            relations=relations
        )
        
        assert len(result.entities) == 2
        assert len(result.relations) == 1
        assert result.entities[0].name == "Alice"
        assert result.relations[0].edge_type == "LIKES"
    
    def test_result_can_be_serialized(self):
        """Test result serialization"""
        result = ExtractionResult(
            entities=[
                ExtractedEntity(
                    label="Person",
                    name="Alice",
                    graph_type=GraphType.INTERNAL
                )
            ],
            relations=[
                ExtractedRelation(
                    edge_type="LIKES",
                    from_entity_name="Alice",
                    to_entity_name="Python",
                    graph_type=GraphType.INTERNAL
                )
            ]
        )
        
        data = result.model_dump()
        
        assert len(data["entities"]) == 1
        assert len(data["relations"]) == 1
        assert data["entities"][0]["name"] == "Alice"

