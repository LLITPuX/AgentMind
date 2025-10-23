"""
Unit tests for schema models

Tests for Pydantic models: Source, BiTemporalMixin, ConceptualNode,
ConceptualEdge, and Statement.

Following TDD approach - these tests verify:
1. Model instantiation
2. Validation logic
3. Serialization/deserialization
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.memory.schema import (
    GraphType,
    SourceType,
    Source,
    BiTemporalMixin,
    ConceptualNode,
    ConceptualEdge,
    Statement,
)


@pytest.mark.unit
class TestGraphType:
    """Tests for GraphType enum"""
    
    def test_graph_type_has_internal_and_external(self):
        """Test that GraphType enum has expected values"""
        assert GraphType.INTERNAL == "internal"
        assert GraphType.EXTERNAL == "external"
    
    def test_graph_type_can_be_created_from_string(self):
        """Test that GraphType can be created from string"""
        assert GraphType("internal") == GraphType.INTERNAL
        assert GraphType("external") == GraphType.EXTERNAL


@pytest.mark.unit
class TestSource:
    """Tests for Source model"""
    
    def test_source_can_be_created(self):
        """Test basic Source instantiation"""
        source = Source(
            name="User_001",
            type=SourceType.USER,
            reliability_score=0.9
        )
        
        assert source.name == "User_001"
        assert source.type == SourceType.USER
        assert source.reliability_score == 0.9
        assert source.metadata == {}
    
    def test_source_has_default_reliability_score(self):
        """Test that reliability_score has default value of 0.5"""
        source = Source(name="Test", type=SourceType.USER)
        assert source.reliability_score == 0.5
    
    def test_source_accepts_metadata(self):
        """Test that Source accepts metadata dict"""
        metadata = {"session_id": "abc123", "ip": "127.0.0.1"}
        source = Source(
            name="User_001",
            type=SourceType.USER,
            metadata=metadata
        )
        
        assert source.metadata == metadata
    
    def test_source_validates_reliability_score_range(self):
        """Test that reliability_score must be between 0.0 and 1.0"""
        # Valid scores
        Source(name="Test", type=SourceType.USER, reliability_score=0.0)
        Source(name="Test", type=SourceType.USER, reliability_score=0.5)
        Source(name="Test", type=SourceType.USER, reliability_score=1.0)
        
        # Invalid scores
        with pytest.raises(ValidationError):
            Source(name="Test", type=SourceType.USER, reliability_score=-0.1)
        
        with pytest.raises(ValidationError):
            Source(name="Test", type=SourceType.USER, reliability_score=1.1)
    
    def test_source_can_be_serialized(self):
        """Test that Source can be converted to dict"""
        source = Source(
            name="User_001",
            type=SourceType.USER,
            reliability_score=0.9
        )
        
        data = source.model_dump()
        
        assert data["name"] == "User_001"
        assert data["type"] == "user"
        assert data["reliability_score"] == 0.9


@pytest.mark.unit
class TestBiTemporalMixin:
    """Tests for BiTemporalMixin"""
    
    def test_bitemporal_mixin_has_default_values(self):
        """Test that BiTemporalMixin has sensible defaults"""
        obj = BiTemporalMixin()
        
        assert obj.valid_from is not None
        assert obj.valid_until == datetime(9999, 12, 31, 23, 59, 59)
        assert obj.tx_time_from is not None
        assert obj.tx_time_to is None
    
    def test_bitemporal_mixin_accepts_custom_values(self):
        """Test that all bitemporal fields can be set"""
        now = datetime.now()
        future = now + timedelta(days=30)
        
        obj = BiTemporalMixin(
            valid_from=now,
            valid_until=future,
            tx_time_from=now,
            tx_time_to=future
        )
        
        assert obj.valid_from == now
        assert obj.valid_until == future
        assert obj.tx_time_from == now
        assert obj.tx_time_to == future
    
    def test_bitemporal_mixin_validates_valid_until_after_valid_from(self):
        """Test that valid_until must be after valid_from"""
        now = datetime.now()
        past = now - timedelta(days=1)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BiTemporalMixin(
                valid_from=now,
                valid_until=past
            )
        
        assert "valid_until must be after valid_from" in str(exc_info.value)
    
    def test_bitemporal_mixin_validates_tx_time_to_after_tx_time_from(self):
        """Test that tx_time_to must be after tx_time_from"""
        now = datetime.now()
        past = now - timedelta(days=1)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            BiTemporalMixin(
                tx_time_from=now,
                tx_time_to=past
            )
        
        assert "tx_time_to must be after tx_time_from" in str(exc_info.value)
    
    def test_bitemporal_mixin_allows_none_tx_time_to(self):
        """Test that tx_time_to can be None (meaning current)"""
        obj = BiTemporalMixin(tx_time_to=None)
        assert obj.tx_time_to is None


@pytest.mark.unit
class TestConceptualNode:
    """Tests for ConceptualNode model"""
    
    def test_conceptual_node_can_be_created(self):
        """Test basic ConceptualNode instantiation"""
        node = ConceptualNode(
            label="Person",
            name="Elon Musk",
            graph_type=GraphType.EXTERNAL
        )
        
        assert node.label == "Person"
        assert node.name == "Elon Musk"
        assert node.graph_type == GraphType.EXTERNAL
        assert node.id is not None  # Auto-generated UUID
        assert node.properties == {}
    
    def test_conceptual_node_generates_unique_ids(self):
        """Test that each node gets a unique ID"""
        node1 = ConceptualNode(label="Person", name="Alice", graph_type=GraphType.INTERNAL)
        node2 = ConceptualNode(label="Person", name="Bob", graph_type=GraphType.INTERNAL)
        
        assert node1.id != node2.id
    
    def test_conceptual_node_accepts_custom_id(self):
        """Test that custom ID can be provided"""
        custom_id = "custom-person-123"
        node = ConceptualNode(
            id=custom_id,
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL
        )
        
        assert node.id == custom_id
    
    def test_conceptual_node_accepts_properties(self):
        """Test that ConceptualNode accepts properties dict"""
        properties = {"age": 30, "occupation": "Engineer"}
        node = ConceptualNode(
            label="Person",
            name="Alice",
            graph_type=GraphType.EXTERNAL,
            properties=properties
        )
        
        assert node.properties == properties
    
    def test_conceptual_node_inherits_bitemporal_fields(self):
        """Test that ConceptualNode has bitemporal fields"""
        node = ConceptualNode(
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL
        )
        
        assert hasattr(node, 'valid_from')
        assert hasattr(node, 'valid_until')
        assert hasattr(node, 'tx_time_from')
        assert hasattr(node, 'tx_time_to')
    
    def test_conceptual_node_validates_bitemporal_constraints(self):
        """Test that ConceptualNode validates bitemporal constraints"""
        now = datetime.now()
        past = now - timedelta(days=1)
        
        # Should raise ValidationError for invalid valid_until
        with pytest.raises(ValidationError):
            ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL,
                valid_from=now,
                valid_until=past
            )
    
    def test_conceptual_node_can_be_serialized(self):
        """Test that ConceptualNode can be converted to dict"""
        node = ConceptualNode(
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL,
            properties={"age": 30}
        )
        
        data = node.model_dump()
        
        assert data["label"] == "Person"
        assert data["name"] == "Alice"
        assert data["graph_type"] == "internal"
        assert data["properties"]["age"] == 30


@pytest.mark.unit
class TestConceptualEdge:
    """Tests for ConceptualEdge model"""
    
    def test_conceptual_edge_can_be_created(self):
        """Test basic ConceptualEdge instantiation"""
        edge = ConceptualEdge(
            edge_type="CEO_OF",
            from_node_id="person-123",
            to_node_id="company-456",
            graph_type=GraphType.EXTERNAL
        )
        
        assert edge.edge_type == "CEO_OF"
        assert edge.from_node_id == "person-123"
        assert edge.to_node_id == "company-456"
        assert edge.graph_type == GraphType.EXTERNAL
        assert edge.id is not None  # Auto-generated UUID
    
    def test_conceptual_edge_generates_unique_ids(self):
        """Test that each edge gets a unique ID"""
        edge1 = ConceptualEdge(
            edge_type="KNOWS",
            from_node_id="person-1",
            to_node_id="person-2",
            graph_type=GraphType.EXTERNAL
        )
        edge2 = ConceptualEdge(
            edge_type="KNOWS",
            from_node_id="person-1",
            to_node_id="person-3",
            graph_type=GraphType.EXTERNAL
        )
        
        assert edge1.id != edge2.id
    
    def test_conceptual_edge_accepts_properties(self):
        """Test that ConceptualEdge accepts properties dict"""
        properties = {"since": "2020-01-01", "strength": 0.8}
        edge = ConceptualEdge(
            edge_type="KNOWS",
            from_node_id="person-1",
            to_node_id="person-2",
            graph_type=GraphType.EXTERNAL,
            properties=properties
        )
        
        assert edge.properties == properties
    
    def test_conceptual_edge_inherits_bitemporal_fields(self):
        """Test that ConceptualEdge has bitemporal fields"""
        edge = ConceptualEdge(
            edge_type="KNOWS",
            from_node_id="person-1",
            to_node_id="person-2",
            graph_type=GraphType.EXTERNAL
        )
        
        assert hasattr(edge, 'valid_from')
        assert hasattr(edge, 'valid_until')
        assert hasattr(edge, 'tx_time_from')
        assert hasattr(edge, 'tx_time_to')
    
    def test_conceptual_edge_can_be_serialized(self):
        """Test that ConceptualEdge can be converted to dict"""
        edge = ConceptualEdge(
            edge_type="CEO_OF",
            from_node_id="person-123",
            to_node_id="company-456",
            graph_type=GraphType.EXTERNAL
        )
        
        data = edge.model_dump()
        
        assert data["edge_type"] == "CEO_OF"
        assert data["from_node_id"] == "person-123"
        assert data["to_node_id"] == "company-456"
        assert data["graph_type"] == "external"


@pytest.mark.unit
class TestStatement:
    """Tests for Statement model"""
    
    def test_statement_can_be_created(self):
        """Test basic Statement instantiation"""
        source = Source(name="User_001", type=SourceType.USER)
        stmt = Statement(
            asserts_about_conceptual_id="node-123",
            source=source,
            attributes={"status": "active"}
        )
        
        assert stmt.asserts_about_conceptual_id == "node-123"
        assert stmt.source.name == "User_001"
        assert stmt.attributes["status"] == "active"
        assert stmt.confidence == 1.0  # Default
        assert stmt.id is not None
    
    def test_statement_accepts_confidence(self):
        """Test that Statement accepts confidence parameter"""
        source = Source(name="User_001", type=SourceType.USER)
        stmt = Statement(
            asserts_about_conceptual_id="node-123",
            source=source,
            confidence=0.75
        )
        
        assert stmt.confidence == 0.75
    
    def test_statement_validates_confidence_range(self):
        """Test that confidence must be between 0.0 and 1.0"""
        source = Source(name="User_001", type=SourceType.USER)
        
        # Valid confidence values
        Statement(asserts_about_conceptual_id="node-123", source=source, confidence=0.0)
        Statement(asserts_about_conceptual_id="node-123", source=source, confidence=0.5)
        Statement(asserts_about_conceptual_id="node-123", source=source, confidence=1.0)
        
        # Invalid confidence values
        with pytest.raises(ValidationError):
            Statement(asserts_about_conceptual_id="node-123", source=source, confidence=-0.1)
        
        with pytest.raises(ValidationError):
            Statement(asserts_about_conceptual_id="node-123", source=source, confidence=1.1)
    
    def test_statement_inherits_bitemporal_fields(self):
        """Test that Statement has bitemporal fields"""
        source = Source(name="User_001", type=SourceType.USER)
        stmt = Statement(
            asserts_about_conceptual_id="node-123",
            source=source
        )
        
        assert hasattr(stmt, 'valid_from')
        assert hasattr(stmt, 'valid_until')
        assert hasattr(stmt, 'tx_time_from')
        assert hasattr(stmt, 'tx_time_to')
    
    def test_statement_can_be_serialized(self):
        """Test that Statement can be converted to dict"""
        source = Source(
            name="Board of Directors",
            type=SourceType.EXTERNAL_API,
            reliability_score=0.9
        )
        stmt = Statement(
            asserts_about_conceptual_id="edge-ceo-123",
            source=source,
            attributes={"status": "terminated"},
            confidence=0.95
        )
        
        data = stmt.model_dump()
        
        assert data["asserts_about_conceptual_id"] == "edge-ceo-123"
        assert data["source"]["name"] == "Board of Directors"
        assert data["attributes"]["status"] == "terminated"
        assert data["confidence"] == 0.95
    
    def test_statement_can_be_deserialized(self):
        """Test that Statement can be created from dict"""
        data = {
            "id": "stmt-123",
            "asserts_about_conceptual_id": "edge-456",
            "source": {
                "name": "Test Source",
                "type": "user",
                "reliability_score": 0.8
            },
            "attributes": {"key": "value"},
            "confidence": 0.9,
            "valid_from": "2025-01-01T00:00:00",
            "valid_until": "2025-12-31T23:59:59",
            "tx_time_from": "2025-10-23T12:00:00",
            "tx_time_to": None
        }
        
        stmt = Statement(**data)
        
        assert stmt.id == "stmt-123"
        assert stmt.source.name == "Test Source"
        assert stmt.confidence == 0.9


@pytest.mark.unit
class TestMultiSourceScenario:
    """
    Tests for the core multi-source truth scenario.
    
    This tests the ability to have multiple conflicting Statements
    about the same ConceptualEdge, as described in the architecture.
    """
    
    def test_multiple_statements_can_reference_same_conceptual_edge(self):
        """
        Test the Elon Musk CEO scenario from Reflexive_Memory_Architecture.md
        
        Two sources make conflicting claims about the same relationship.
        Both statements should coexist without overwriting each other.
        """
        # Source 1: Board of Directors says CEO status ended
        source1 = Source(
            name="Board of Directors",
            type=SourceType.EXTERNAL_API,
            reliability_score=0.9
        )
        
        stmt1 = Statement(
            asserts_about_conceptual_id="edge-elon-ceo-tesla",
            source=source1,
            attributes={"status": "terminated", "reason": "board_decision"},
            valid_from=datetime(2020, 1, 1),
            valid_until=datetime(2025, 10, 23),
            confidence=0.95
        )
        
        # Source 2: Lawyer says CEO status continues
        source2 = Source(
            name="Legal Representative",
            type=SourceType.EXTERNAL_API,
            reliability_score=0.7
        )
        
        stmt2 = Statement(
            asserts_about_conceptual_id="edge-elon-ceo-tesla",
            source=source2,
            attributes={"status": "active", "reason": "termination_invalid"},
            valid_from=datetime(2020, 1, 1),
            valid_until=datetime(9999, 12, 31, 23, 59, 59),
            confidence=0.8
        )
        
        # Both statements reference the same edge but have different IDs
        assert stmt1.id != stmt2.id
        assert stmt1.asserts_about_conceptual_id == stmt2.asserts_about_conceptual_id
        
        # They have different sources
        assert stmt1.source.name != stmt2.source.name
        
        # They have conflicting valid_until dates
        assert stmt1.valid_until != stmt2.valid_until
        
        # Both are valid Pydantic models
        assert stmt1.model_dump() is not None
        assert stmt2.model_dump() is not None

