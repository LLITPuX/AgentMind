"""
Integration tests for consolidation process.

Tests the consolidation workflow components without requiring real LLM API.
"""

import pytest
from datetime import datetime
import os
from unittest.mock import Mock, patch, MagicMock

from src.memory import (
    ShortTermMemoryBuffer,
    MemoryManager,
    Observation,
    ConsolidationGraph,
    ConceptualNode,
    GraphType,
    ExtractedEntity,
    ExtractedRelation,
    ExtractionResult
)
from src.memory.consolidation import ConsolidationState


@pytest.mark.integration
class TestConsolidationIntegration:
    """Integration tests for full consolidation workflow"""
    
    @pytest.fixture
    def setup_memory(self, falkordb_host, falkordb_port):
        """Setup STM, LTM, and consolidation graph"""
        stm = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_consolidation_stm"
        )
        
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        
        # Clear STM and graph
        stm.clear()
        try:
            manager.clear_graph("agentmind_ltm")
        except:
            pass
        
        yield stm, manager
        
        # Cleanup
        stm.clear()
        try:
            manager.delete_graph("agentmind_ltm")
        except:
            pass
    
    def test_save_to_ltm_creates_edges_between_entities(self, setup_memory):
        """Test save_to_ltm creates edges between entities"""
        stm, manager = setup_memory
        
        # Create two nodes first
        node1 = ConceptualNode(
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL
        )
        node2 = ConceptualNode(
            label="Language",
            name="Python",
            graph_type=GraphType.EXTERNAL
        )
        
        node1_id = manager.create_conceptual_node(node1, "agentmind_ltm")
        node2_id = manager.create_conceptual_node(node2, "agentmind_ltm")
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create state with relation between existing entities
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [],
            "extracted_relations": [
                ExtractedRelation(
                    edge_type="LIKES",
                    from_entity_name="Alice",
                    to_entity_name="Python",
                    graph_type=GraphType.INTERNAL,
                    properties={}
                )
            ],
            "deduplicated_nodes": [node1_id, node2_id],
            "created_statements": [],
            "entity_id_map": {"Alice": node1_id, "Python": node2_id},
            "messages": [],
            "error": None
        }
        
        # Call save_to_ltm node
        updated_state = consolidation.save_to_ltm_node(state)
        
        # Verify edge created
        graph = manager.get_graph("agentmind_ltm")
        result = graph.query("""
            MATCH (a:ConceptualNode {name: 'Alice'})-[r:CONCEPTUAL_EDGE {edge_type: 'LIKES'}]->(p:ConceptualNode {name: 'Python'})
            WHERE r.tx_time_to IS NULL
            RETURN r
        """)
        assert len(result.result_set) == 1
    
    def test_fetch_observations_node(self, setup_memory):
        """Test fetch_observations_node retrieves from STM"""
        stm, manager = setup_memory
        
        # Add observations
        obs = Observation(content="Test observation", timestamp=datetime.now())
        stm.add(obs)
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create initial state
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [],
            "extracted_relations": [],
            "deduplicated_nodes": [],
            "created_statements": [],
            "entity_id_map": {},
            "messages": [],
            "error": None
        }
        
        # Call fetch_observations node
        updated_state = consolidation.fetch_observations_node(state)
        
        assert len(updated_state["observations"]) == 1
        assert updated_state["observations"][0].content == "Test observation"
    
    def test_deduplicate_entities_node_with_exact_match(self, setup_memory):
        """Test deduplication finds existing node"""
        stm, manager = setup_memory
        
        # Create existing node
        existing_node = ConceptualNode(
            label="Person",
            name="Alice",
            graph_type=GraphType.INTERNAL
        )
        node_id = manager.create_conceptual_node(existing_node, "agentmind_ltm")
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create state with extracted entity matching existing node
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [
                ExtractedEntity(
                    label="Person",
                    name="Alice",
                    graph_type=GraphType.INTERNAL,
                    properties={}
                )
            ],
            "extracted_relations": [],
            "deduplicated_nodes": [],
            "created_statements": [],
            "entity_id_map": {},
            "messages": [],
            "error": None
        }
        
        # Call deduplicate node
        updated_state = consolidation.deduplicate_entities_node(state)
        
        # Should find existing node
        assert "entity_id_map" in updated_state
        assert "Alice" in updated_state["entity_id_map"]
        assert updated_state["entity_id_map"]["Alice"] == node_id
    
    def test_save_to_ltm_node_creates_new_entities(self, setup_memory):
        """Test save_to_ltm creates new entities"""
        stm, manager = setup_memory
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create state with entity marked for creation
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [
                ExtractedEntity(
                    label="Language",
                    name="Python",
                    graph_type=GraphType.EXTERNAL,
                    properties={"type": "programming"}
                )
            ],
            "extracted_relations": [],
            "deduplicated_nodes": [],
            "created_statements": [],
            "entity_id_map": {"Python": None},  # None means needs creation
            "messages": [],
            "error": None
        }
        
        # Call save_to_ltm node
        updated_state = consolidation.save_to_ltm_node(state)
        
        # Should create node
        assert len(updated_state["deduplicated_nodes"]) > 0
        assert len(updated_state["created_statements"]) > 0
        
        # Verify node exists in database
        graph = manager.get_graph("agentmind_ltm")
        result = graph.query("""
            MATCH (n:ConceptualNode {label: 'Language', name: 'Python'})
            WHERE n.tx_time_to IS NULL
            RETURN n
        """)
        assert len(result.result_set) == 1


    def test_consolidation_stores_embeddings_for_nodes(self, setup_memory):
        """Test that consolidation stores embeddings for created nodes"""
        stm, manager = setup_memory
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create state with entity marked for creation
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [
                ExtractedEntity(
                    label="Language",
                    name="Python",
                    graph_type=GraphType.EXTERNAL,
                    properties={"type": "programming"}
                )
            ],
            "extracted_relations": [],
            "deduplicated_nodes": [],
            "created_statements": [],
            "entity_id_map": {"Python": None},  # None means needs creation
            "messages": [],
            "error": None
        }
        
        # Call save_to_ltm node
        updated_state = consolidation.save_to_ltm_node(state)
        
        # Get the created node ID
        node_id = updated_state["entity_id_map"]["Python"]
        assert node_id is not None
        
        # Verify embedding was stored
        graph = manager.get_graph("agentmind_ltm")
        result = graph.query("""
            MATCH (n:ConceptualNode {id: $node_id})
            RETURN n.embedding AS embedding
        """, {"node_id": node_id})
        
        assert len(result.result_set) == 1
        # Embedding should be stored (not None)
        assert result.result_set[0][0] is not None
    
    def test_embeddings_are_searchable_after_consolidation(self, setup_memory):
        """Test that embeddings created during consolidation are searchable"""
        stm, manager = setup_memory
        
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Create two entities
        state: ConsolidationState = {
            "observations": [],
            "extracted_entities": [
                ExtractedEntity(
                    label="Language",
                    name="Python",
                    graph_type=GraphType.EXTERNAL,
                    properties={"type": "programming"}
                ),
                ExtractedEntity(
                    label="Language",
                    name="JavaScript",
                    graph_type=GraphType.EXTERNAL,
                    properties={"type": "programming"}
                )
            ],
            "extracted_relations": [],
            "deduplicated_nodes": [],
            "created_statements": [],
            "entity_id_map": {"Python": None, "JavaScript": None},
            "messages": [],
            "error": None
        }
        
        # Create nodes with embeddings
        consolidation.save_to_ltm_node(state)
        
        # Now try vector search for "Python"
        from src.memory.embeddings import get_embedding_manager
        emb_manager = get_embedding_manager(force_new=True)
        query_embedding = emb_manager.generate_embedding("Python programming language")
        
        results = manager.vector_search_nodes(
            query_embedding,
            top_k=5,
            graph_name="agentmind_ltm"
        )
        
        # Should find at least one result
        assert len(results) >= 1
        # Python should be in the results
        result_names = [r['name'] for r in results]
        assert 'Python' in result_names


@pytest.mark.integration
class TestConsolidationAPI:
    """Tests for consolidation API endpoint"""
    
    @pytest.mark.skip(reason="Requires FastAPI test client - implement later")
    def test_consolidation_endpoint_success(self):
        """Test /api/consolidate endpoint with successful consolidation"""
        pass
    
    @pytest.mark.skip(reason="Requires FastAPI test client - implement later")
    def test_consolidation_status_endpoint(self):
        """Test /api/consolidation/status endpoint"""
        pass

