"""
Tests for vector search operations.

Tests the vector embedding storage and vector similarity search functionality.
"""

import pytest
from datetime import datetime
from typing import List

from src.memory import MemoryManager, ConceptualNode, GraphType


@pytest.mark.integration
class TestVectorEmbeddingStorage:
    """Tests for storing embeddings in nodes"""
    
    def test_store_embedding_for_node(self, falkordb_host, falkordb_port):
        """Test that we can store an embedding vector for a node"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_store")
        
        try:
            # Create a node
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            node_id = manager.create_conceptual_node(node, "test_vector_store")
            
            # Store embedding
            embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            manager.store_node_embedding(node_id, embedding, "test_vector_store")
            
            # Verify embedding was stored
            result = graph.query("""
                MATCH (n:ConceptualNode {id: $node_id})
                RETURN n.embedding AS embedding
            """, {"node_id": node_id})
            
            assert len(result.result_set) == 1
            # Embedding should be stored
            assert result.result_set[0][0] is not None
            
        finally:
            graph.delete()
    
    def test_store_embedding_for_nonexistent_node_raises_error(self, falkordb_host, falkordb_port):
        """Test that storing embedding for nonexistent node raises error"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_error")
        
        try:
            embedding = [0.1, 0.2, 0.3]
            
            with pytest.raises(RuntimeError, match="Node with id .* not found"):
                manager.store_node_embedding("nonexistent_id", embedding, "test_vector_error")
                
        finally:
            graph.delete()


@pytest.mark.integration
class TestVectorSearch:
    """Tests for vector similarity search"""
    
    def test_vector_search_returns_similar_nodes(self, falkordb_host, falkordb_port):
        """Test that vector search finds similar nodes"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_search")
        
        try:
            # Create nodes with embeddings
            node1 = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            node1_id = manager.create_conceptual_node(node1, "test_vector_search")
            embedding1 = [1.0, 0.0, 0.0]
            manager.store_node_embedding(node1_id, embedding1, "test_vector_search")
            
            node2 = ConceptualNode(
                label="Person",
                name="Bob",
                graph_type=GraphType.INTERNAL
            )
            node2_id = manager.create_conceptual_node(node2, "test_vector_search")
            embedding2 = [0.9, 0.1, 0.0]  # Very similar to node1
            manager.store_node_embedding(node2_id, embedding2, "test_vector_search")
            
            node3 = ConceptualNode(
                label="Person",
                name="Charlie",
                graph_type=GraphType.INTERNAL
            )
            node3_id = manager.create_conceptual_node(node3, "test_vector_search")
            embedding3 = [0.0, 0.0, 1.0]  # Very different
            manager.store_node_embedding(node3_id, embedding3, "test_vector_search")
            
            # Search with query similar to node1
            query_embedding = [0.95, 0.05, 0.0]
            results = manager.vector_search_nodes(
                query_embedding,
                top_k=2,
                graph_name="test_vector_search"
            )
            
            # Should return top 2 most similar
            assert len(results) >= 1
            # Results should have similarity scores
            assert 'similarity_score' in results[0]
            # Most similar should be Alice or Bob
            result_names = [r['name'] for r in results]
            assert 'Alice' in result_names or 'Bob' in result_names
            
        finally:
            graph.delete()
    
    def test_vector_search_filters_by_graph_type(self, falkordb_host, falkordb_port):
        """Test that vector search can filter by graph_type"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_filter")
        
        try:
            # Create internal node
            node_internal = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            internal_id = manager.create_conceptual_node(node_internal, "test_vector_filter")
            embedding_internal = [1.0, 0.0, 0.0]
            manager.store_node_embedding(internal_id, embedding_internal, "test_vector_filter")
            
            # Create external node
            node_external = ConceptualNode(
                label="Person",
                name="Bob",
                graph_type=GraphType.EXTERNAL
            )
            external_id = manager.create_conceptual_node(node_external, "test_vector_filter")
            embedding_external = [0.9, 0.1, 0.0]  # Very similar embedding
            manager.store_node_embedding(external_id, embedding_external, "test_vector_filter")
            
            # Search only INTERNAL graph
            query_embedding = [1.0, 0.0, 0.0]
            results = manager.vector_search_nodes(
                query_embedding,
                top_k=5,
                graph_type=GraphType.INTERNAL,
                graph_name="test_vector_filter"
            )
            
            # Should only return internal nodes
            assert len(results) >= 1
            for result in results:
                assert result['graph_type'] == 'internal'
            
            # Verify Alice is in results, Bob is not
            result_names = [r['name'] for r in results]
            assert 'Alice' in result_names
            assert 'Bob' not in result_names
            
        finally:
            graph.delete()
    
    def test_vector_search_returns_empty_for_no_matches(self, falkordb_host, falkordb_port):
        """Test that vector search returns empty list when no nodes have embeddings"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_empty")
        
        try:
            # Create node WITHOUT embedding
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            manager.create_conceptual_node(node, "test_vector_empty")
            
            # Search
            query_embedding = [1.0, 0.0, 0.0]
            results = manager.vector_search_nodes(
                query_embedding,
                top_k=5,
                graph_name="test_vector_empty"
            )
            
            # Should return empty (no nodes with embeddings)
            assert len(results) == 0
            
        finally:
            graph.delete()
    
    def test_vector_search_respects_top_k_limit(self, falkordb_host, falkordb_port):
        """Test that vector search respects top_k parameter"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_vector_topk")
        
        try:
            # Create 5 nodes with embeddings
            for i in range(5):
                node = ConceptualNode(
                    label="Person",
                    name=f"Person{i}",
                    graph_type=GraphType.INTERNAL
                )
                node_id = manager.create_conceptual_node(node, "test_vector_topk")
                embedding = [float(i)/10, 0.0, 0.0]
                manager.store_node_embedding(node_id, embedding, "test_vector_topk")
            
            # Search with top_k=2
            query_embedding = [0.5, 0.0, 0.0]
            results = manager.vector_search_nodes(
                query_embedding,
                top_k=2,
                graph_name="test_vector_topk"
            )
            
            # Should return at most 2 results
            assert len(results) <= 2
            
        finally:
            graph.delete()

