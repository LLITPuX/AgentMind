"""
Tests for deduplication logic.

Tests exact match and vector similarity deduplication without full E2E workflow.
"""

import pytest
from datetime import datetime
import os
from unittest.mock import Mock, patch

from src.memory import (
    MemoryManager,
    ConceptualNode,
    GraphType,
    EmbeddingManager
)


@pytest.mark.integration
class TestExactMatchDeduplication:
    """Tests for exact match deduplication strategy"""
    
    def test_exact_match_finds_existing_node(self, falkordb_host, falkordb_port):
        """Test that exact match finds existing node"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_exact_match")
        
        try:
            # Create a node
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            
            node_id = manager.create_conceptual_node(node, "test_exact_match")
            
            # Try to find it with exact match query
            query = """
            MATCH (n:ConceptualNode {label: $label, name: $name, graph_type: $graph_type})
            WHERE n.tx_time_to IS NULL
            RETURN n.id AS id
            """
            
            result = graph.query(query, {
                "label": "Person",
                "name": "Alice",
                "graph_type": "internal"
            })
            
            assert len(result.result_set) == 1
            assert result.result_set[0][0] == node_id
            
        finally:
            graph.delete()
    
    def test_exact_match_returns_nothing_for_similar_name(self, falkordb_host, falkordb_port):
        """Test that exact match doesn't match similar but different names"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_exact_no_match")
        
        try:
            # Create "Alice"
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            
            manager.create_conceptual_node(node, "test_exact_no_match")
            
            # Try to find "Alicia" (similar but different)
            query = """
            MATCH (n:ConceptualNode {label: $label, name: $name, graph_type: $graph_type})
            WHERE n.tx_time_to IS NULL
            RETURN n.id AS id
            """
            
            result = graph.query(query, {
                "label": "Person",
                "name": "Alicia",
                "graph_type": "internal"
            })
            
            # Should not find anything
            assert len(result.result_set) == 0
            
        finally:
            graph.delete()


@pytest.mark.unit
class TestVectorSimilarity:
    """Tests for vector similarity calculations"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-not-real"})
    def test_embedding_manager_can_be_created(self):
        """Test that EmbeddingManager can be created"""
        manager = EmbeddingManager(api_key="sk-test-key")
        
        assert manager is not None
        assert manager.api_key == "sk-test-key"
    
    def test_cosine_similarity_calculation(self):
        """Test cosine similarity calculation"""
        manager = EmbeddingManager(api_key="sk-test-key")
        
        # Identical vectors should have similarity 1.0
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = manager.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001
        
        # Orthogonal vectors should have similarity 0.0
        vec3 = [1.0, 0.0]
        vec4 = [0.0, 1.0]
        similarity = manager.cosine_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 0.001
        
        # Opposite vectors should have similarity 0.0 (clamped)
        vec5 = [1.0, 0.0]
        vec6 = [-1.0, 0.0]
        similarity = manager.cosine_similarity(vec5, vec6)
        assert 0.0 <= similarity <= 1.0
    
    def test_find_most_similar_with_threshold(self):
        """Test finding most similar embedding"""
        manager = EmbeddingManager(api_key="sk-test-key")
        
        query = [1.0, 2.0, 3.0]
        candidates = [
            [1.1, 2.1, 3.1],  # Very similar
            [5.0, 6.0, 7.0],  # Less similar
            [-1.0, -2.0, -3.0]  # Opposite
        ]
        
        # With reasonable threshold (0.85), should find first candidate
        idx, sim = manager.find_most_similar(query, candidates, threshold=0.85)
        assert idx == 0
        assert sim > 0.85
        
        # With low threshold (0.0), should find most similar (first one)
        idx, sim = manager.find_most_similar(query, candidates, threshold=0.0)
        assert idx == 0  # First candidate is most similar
    
    def test_find_most_similar_with_empty_candidates(self):
        """Test finding similar with no candidates"""
        manager = EmbeddingManager(api_key="sk-test-key")
        
        query = [1.0, 2.0, 3.0]
        candidates = []
        
        idx, sim = manager.find_most_similar(query, candidates)
        assert idx == -1
        assert sim == 0.0

