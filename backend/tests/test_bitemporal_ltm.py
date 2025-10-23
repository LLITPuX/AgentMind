"""
Integration tests for bitemporal long-term memory operations.

These tests verify the Stage 2 implementation:
1. Creating ConceptualNodes with bitemporal fields
2. Expiring entities (setting tx_time_to)
3. Querying with temporal constraints
4. Filtering by graph_type (internal/external)
5. Creating and querying Statements
6. Multi-source truth scenario (Elon Musk CEO example)
"""

import pytest
from datetime import datetime, timedelta

from src.memory.manager import MemoryManager
from src.memory.schema import (
    ConceptualNode,
    ConceptualEdge,
    Statement,
    Source,
    GraphType,
    SourceType,
)


@pytest.mark.integration
class TestBiTemporalNodeCreation:
    """Tests for creating ConceptualNodes with bitemporal fields"""
    
    def test_create_bitemporal_node_stores_time_fields(self, falkordb_host, falkordb_port):
        """
        Test that ConceptualNode with bitemporal fields is stored correctly.
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_bitemporal_node")
        
        try:
            # Create node with specific temporal values
            now = datetime.now()
            future = now + timedelta(days=365)
            
            node = ConceptualNode(
                label="Person",
                name="Elon Musk",
                graph_type=GraphType.EXTERNAL,
                valid_from=now,
                valid_until=future,
                tx_time_from=now,
                properties={"occupation": "CEO"}
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_bitemporal_node")
            
            assert node_id == node.id
            
            # Verify node was created with correct fields
            result = graph.query(f"MATCH (n:ConceptualNode {{id: '{node_id}'}}) RETURN n")
            assert len(result.result_set) == 1
            
            stored_node = result.result_set[0][0]
            assert stored_node.properties['label'] == "Person"
            assert stored_node.properties['name'] == "Elon Musk"
            assert stored_node.properties['graph_type'] == "external"
            assert stored_node.properties['valid_from'] is not None
            assert stored_node.properties['valid_until'] is not None
            assert stored_node.properties['tx_time_from'] is not None
            
        finally:
            graph.delete()
    
    def test_create_node_with_default_temporal_values(self, falkordb_host, falkordb_port):
        """Test that nodes get sensible default temporal values"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_default_temporal")
        
        try:
            node = ConceptualNode(
                label="Concept",
                name="Test Concept",
                graph_type=GraphType.INTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_default_temporal")
            
            # Verify defaults
            result = graph.query(f"MATCH (n:ConceptualNode {{id: '{node_id}'}}) RETURN n")
            stored_node = result.result_set[0][0]
            
            # FalkorDB doesn't store None/null values as properties, so check if key doesn't exist
            assert 'tx_time_to' not in stored_node.properties or stored_node.properties['tx_time_to'] is None
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestBiTemporalNodeExpiration:
    """Tests for expiring (retiring) ConceptualNodes"""
    
    def test_expire_node_sets_tx_time_to(self, falkordb_host, falkordb_port):
        """Test that expiring a node sets its tx_time_to"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_expire_node")
        
        try:
            # Create node
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_expire_node")
            
            # Verify tx_time_to is None initially (or doesn't exist)
            result = graph.query(f"MATCH (n:ConceptualNode {{id: '{node_id}'}}) RETURN n")
            stored_props = result.result_set[0][0].properties
            assert 'tx_time_to' not in stored_props or stored_props['tx_time_to'] is None
            
            # Expire the node
            expiry_time = datetime.now()
            manager.expire_node(node_id, expiry_time, graph_name="test_expire_node")
            
            # Verify tx_time_to is now set
            result = graph.query(f"MATCH (n:ConceptualNode {{id: '{node_id}'}}) RETURN n")
            stored_node = result.result_set[0][0]
            assert stored_node.properties['tx_time_to'] is not None
            assert stored_node.properties['tx_time_to'] == expiry_time.isoformat()
            
        finally:
            graph.delete()
    
    def test_expired_node_still_exists(self, falkordb_host, falkordb_port):
        """Test that expiring doesn't delete the node, just marks it"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_expired_exists")
        
        try:
            node = ConceptualNode(
                label="Person",
                name="Bob",
                graph_type=GraphType.EXTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_expired_exists")
            
            # Expire it
            manager.expire_node(node_id, datetime.now(), graph_name="test_expired_exists")
            
            # Verify node still exists
            result = graph.query(f"MATCH (n:ConceptualNode {{id: '{node_id}'}}) RETURN count(n) AS count")
            assert result.result_set[0][0] == 1
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestBiTemporalQuerying:
    """Tests for querying with temporal constraints"""
    
    def test_query_nodes_at_specific_time(self, falkordb_host, falkordb_port):
        """Test querying nodes that were valid at a specific point in time"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_temporal_query")
        
        try:
            base_time = datetime(2025, 1, 1)
            
            # Create 3 nodes with different temporal ranges
            # Node 1: Valid Jan-Mar
            node1 = ConceptualNode(
                label="Project",
                name="Project Alpha",
                graph_type=GraphType.EXTERNAL,
                valid_from=datetime(2025, 1, 1),
                valid_until=datetime(2025, 3, 31),
                tx_time_from=base_time
            )
            
            # Node 2: Valid Feb-Jun
            node2 = ConceptualNode(
                label="Project",
                name="Project Beta",
                graph_type=GraphType.EXTERNAL,
                valid_from=datetime(2025, 2, 1),
                valid_until=datetime(2025, 6, 30),
                tx_time_from=base_time
            )
            
            # Node 3: Valid Jul-Dec
            node3 = ConceptualNode(
                label="Project",
                name="Project Gamma",
                graph_type=GraphType.EXTERNAL,
                valid_from=datetime(2025, 7, 1),
                valid_until=datetime(2025, 12, 31),
                tx_time_from=base_time
            )
            
            manager.create_conceptual_node(node1, graph_name="test_temporal_query")
            manager.create_conceptual_node(node2, graph_name="test_temporal_query")
            manager.create_conceptual_node(node3, graph_name="test_temporal_query")
            
            # Query for February 15: should return nodes 1 and 2
            feb_15 = datetime(2025, 2, 15)
            nodes = manager.query_nodes_at_time(
                label="Project",
                valid_time=feb_15,
                tx_time=datetime.now(),
                graph_name="test_temporal_query"
            )
            
            assert len(nodes) == 2
            node_names = [n.get('name') for n in nodes]
            assert "Project Alpha" in node_names
            assert "Project Beta" in node_names
            assert "Project Gamma" not in node_names
            
            # Query for August 1: should return only node 3
            aug_1 = datetime(2025, 8, 1)
            nodes = manager.query_nodes_at_time(
                label="Project",
                valid_time=aug_1,
                tx_time=datetime.now(),
                graph_name="test_temporal_query"
            )
            
            assert len(nodes) == 1
            assert nodes[0].get('name') == "Project Gamma"
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestGraphTypeSeparation:
    """Tests for Internal vs External graph separation"""
    
    def test_filter_nodes_by_graph_type(self, falkordb_host, falkordb_port):
        """Test that we can filter nodes by graph_type"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_graph_type")
        
        try:
            # Create internal nodes
            internal_node = ConceptualNode(
                label="AgentIdentity",
                name="My Purpose",
                graph_type=GraphType.INTERNAL
            )
            
            # Create external nodes
            external_node = ConceptualNode(
                label="AgentIdentity",
                name="External Fact",
                graph_type=GraphType.EXTERNAL
            )
            
            manager.create_conceptual_node(internal_node, graph_name="test_graph_type")
            manager.create_conceptual_node(external_node, graph_name="test_graph_type")
            
            # Query with graph_type filter
            now = datetime.now()
            internal_nodes = manager.query_nodes_at_time(
                label="AgentIdentity",
                valid_time=now,
                tx_time=now,
                graph_type=GraphType.INTERNAL,
                graph_name="test_graph_type"
            )
            
            external_nodes = manager.query_nodes_at_time(
                label="AgentIdentity",
                valid_time=now,
                tx_time=now,
                graph_type=GraphType.EXTERNAL,
                graph_name="test_graph_type"
            )
            
            assert len(internal_nodes) == 1
            assert internal_nodes[0].get('name') == "My Purpose"
            
            assert len(external_nodes) == 1
            assert external_nodes[0].get('name') == "External Fact"
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestConceptualEdges:
    """Tests for creating ConceptualEdges"""
    
    def test_create_edge_between_nodes(self, falkordb_host, falkordb_port):
        """Test creating an edge between two nodes"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_edges")
        
        try:
            # Create two nodes
            person = ConceptualNode(
                label="Person",
                name="Elon Musk",
                graph_type=GraphType.EXTERNAL
            )
            
            company = ConceptualNode(
                label="Company",
                name="Tesla",
                graph_type=GraphType.EXTERNAL
            )
            
            person_id = manager.create_conceptual_node(person, graph_name="test_edges")
            company_id = manager.create_conceptual_node(company, graph_name="test_edges")
            
            # Create edge
            edge = ConceptualEdge(
                edge_type="CEO_OF",
                from_node_id=person_id,
                to_node_id=company_id,
                graph_type=GraphType.EXTERNAL
            )
            
            edge_id = manager.create_conceptual_edge(edge, graph_name="test_edges")
            
            assert edge_id == edge.id
            
            # Verify edge exists
            result = graph.query("""
                MATCH (p:ConceptualNode)-[r:CONCEPTUAL_EDGE]->(c:ConceptualNode)
                WHERE r.id = $edge_id
                RETURN r, p.name, c.name
            """, {"edge_id": edge_id})
            
            assert len(result.result_set) == 1
            assert result.result_set[0][1] == "Elon Musk"
            assert result.result_set[0][2] == "Tesla"
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestStatements:
    """Tests for creating and querying Statements"""
    
    def test_create_statement_about_node(self, falkordb_host, falkordb_port):
        """Test creating a Statement about a ConceptualNode"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_statements")
        
        try:
            # Create a node
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_statements")
            
            # Create a statement about this node
            source = Source(
                name="User_001",
                type=SourceType.USER,
                reliability_score=1.0
            )
            
            statement = Statement(
                asserts_about_conceptual_id=node_id,
                source=source,
                attributes={"likes": "Pydantic code examples"},
                confidence=0.9
            )
            
            stmt_id = manager.create_statement(statement, graph_name="test_statements")
            
            assert stmt_id == statement.id
            
            # Verify statement exists and links to node
            result = graph.query("""
                MATCH (s:Statement {id: $stmt_id})-[:ASSERTS_ABOUT]->(n:ConceptualNode)
                RETURN s, n.name
            """, {"stmt_id": stmt_id})
            
            assert len(result.result_set) == 1
            assert result.result_set[0][1] == "Alice"
            
        finally:
            graph.delete()
    
    def test_get_statements_for_concept(self, falkordb_host, falkordb_port):
        """Test retrieving all statements about a concept"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_get_statements")
        
        try:
            # Create a node
            node = ConceptualNode(
                label="Person",
                name="Bob",
                graph_type=GraphType.EXTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, graph_name="test_get_statements")
            
            # Create multiple statements about this node
            source1 = Source(name="Source A", type=SourceType.USER)
            source2 = Source(name="Source B", type=SourceType.EXTERNAL_API)
            
            stmt1 = Statement(
                asserts_about_conceptual_id=node_id,
                source=source1,
                attributes={"status": "active"}
            )
            
            stmt2 = Statement(
                asserts_about_conceptual_id=node_id,
                source=source2,
                attributes={"status": "inactive"}
            )
            
            manager.create_statement(stmt1, graph_name="test_get_statements")
            manager.create_statement(stmt2, graph_name="test_get_statements")
            
            # Retrieve all statements
            statements = manager.get_statements_for_concept(node_id, graph_name="test_get_statements")
            
            assert len(statements) == 2
            
        finally:
            graph.delete()


@pytest.mark.integration
class TestMultiSourceTruth:
    """
    Test the Elon Musk CEO scenario from Reflexive_Memory_Architecture.md
    
    Two different sources make conflicting claims about the same relationship.
    This tests our ability to handle multi-source truth.
    """
    
    def test_conflicting_statements_about_same_edge(self, falkordb_host, falkordb_port):
        """
        Test the core scenario: two sources, conflicting claims, both coexist.
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_multi_source")
        
        try:
            # Create Person and Company nodes
            person = ConceptualNode(
                label="Person",
                name="Elon Musk",
                graph_type=GraphType.EXTERNAL
            )
            
            company = ConceptualNode(
                label="Company",
                name="Tesla",
                graph_type=GraphType.EXTERNAL
            )
            
            person_id = manager.create_conceptual_node(person, graph_name="test_multi_source")
            company_id = manager.create_conceptual_node(company, graph_name="test_multi_source")
            
            # Create the CEO_OF edge
            edge = ConceptualEdge(
                edge_type="CEO_OF",
                from_node_id=person_id,
                to_node_id=company_id,
                graph_type=GraphType.EXTERNAL,
                valid_from=datetime(2020, 1, 1)
            )
            
            edge_id = manager.create_conceptual_edge(edge, graph_name="test_multi_source")
            
            # Source 1: Board of Directors says CEO status ended on Oct 23
            source_board = Source(
                name="Board of Directors",
                type=SourceType.EXTERNAL_API,
                reliability_score=0.9
            )
            
            stmt1 = Statement(
                asserts_about_conceptual_id=edge_id,
                source=source_board,
                attributes={"status": "terminated", "reason": "board_decision"},
                valid_from=datetime(2020, 1, 1),
                valid_until=datetime(2025, 10, 23),
                confidence=0.95
            )
            
            # Source 2: Lawyer says CEO status continues indefinitely
            source_lawyer = Source(
                name="Legal Representative",
                type=SourceType.EXTERNAL_API,
                reliability_score=0.7
            )
            
            stmt2 = Statement(
                asserts_about_conceptual_id=edge_id,
                source=source_lawyer,
                attributes={"status": "active", "reason": "termination_invalid"},
                valid_from=datetime(2020, 1, 1),
                valid_until=datetime(9999, 12, 31, 23, 59, 59),
                confidence=0.8
            )
            
            stmt1_id = manager.create_statement(stmt1, graph_name="test_multi_source")
            stmt2_id = manager.create_statement(stmt2, graph_name="test_multi_source")
            
            # Retrieve all statements about the edge
            statements = manager.get_statements_for_concept(edge_id, graph_name="test_multi_source")
            
            # Both statements should exist independently
            assert len(statements) == 2
            
            # Verify they have different sources
            sources = [s.get('source_name') for s in statements]
            assert "Board of Directors" in sources
            assert "Legal Representative" in sources
            
            # Verify they have different valid_until dates
            valid_untils = [s.get('valid_until') for s in statements]
            assert len(set(valid_untils)) == 2  # Two different dates
            
            # This demonstrates multi-source truth:
            # - The agent doesn't have to choose one "correct" version
            # - Both claims coexist in the graph
            # - The agent can reason about conflicting information
            # - Each claim maintains its source attribution
            
        finally:
            graph.delete()

