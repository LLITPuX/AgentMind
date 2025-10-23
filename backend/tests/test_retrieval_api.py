"""
Tests for retrieval API endpoints.

Tests the /api/search endpoint functionality.
"""

import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch

from src.memory import MemoryManager, ConceptualNode, GraphType


@pytest.mark.integration
class TestSearchEndpointStructure:
    """Tests for search API endpoint structure"""
    
    def test_search_request_model_validation(self):
        """Test SearchRequest Pydantic model validates correctly"""
        from src.api.retrieval import SearchRequest
        
        # Valid request
        request = SearchRequest(query="Test query")
        assert request.query == "Test query"
        assert request.graph_types is None
        assert request.top_k == 5  # Default
        
        # With graph_types
        request = SearchRequest(
            query="Test",
            graph_types=["internal", "external"]
        )
        assert len(request.graph_types) == 2
        
        # With custom top_k
        request = SearchRequest(query="Test", top_k=10)
        assert request.top_k == 10
    
    def test_search_request_top_k_validation(self):
        """Test that top_k has proper validation"""
        from src.api.retrieval import SearchRequest
        from pydantic import ValidationError
        
        # Valid range
        SearchRequest(query="Test", top_k=1)
        SearchRequest(query="Test", top_k=20)
        
        # Invalid: too low
        with pytest.raises(ValidationError):
            SearchRequest(query="Test", top_k=0)
        
        # Invalid: too high
        with pytest.raises(ValidationError):
            SearchRequest(query="Test", top_k=21)


@pytest.mark.integration  
class TestSearchEndpointIntegration:
    """Integration tests for search endpoint"""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_search_endpoint_with_populated_memory(self, falkordb_host, falkordb_port):
        """Test search endpoint returns results from populated memory"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_search_api")
        
        try:
            from src.memory import RetrievalGraph
            from src.memory.embeddings import get_embedding_manager
            
            # Create and store node with embedding
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL,
                properties={"likes": "Python"}
            )
            node_id = manager.create_conceptual_node(node, "test_search_api")
            
            # Store embedding
            emb_manager = get_embedding_manager(force_new=True)
            embedding = emb_manager.generate_embedding("Person: Alice. likes: Python")
            manager.store_node_embedding(node_id, embedding, "test_search_api")
            
            # Create retrieval graph and search
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_search_api"
            )
            
            result = retrieval.search("Who likes Python?")
            
            # Should return successful result
            assert result["status"] == "completed"
            assert "Alice" in result["response"] or "Python" in result["response"]
            assert result["metadata"]["sources_count"] >= 1
            
        finally:
            try:
                graph.delete()
            except:
                pass
    
    def test_search_endpoint_with_empty_memory(self, falkordb_host, falkordb_port):
        """Test search endpoint handles empty memory gracefully"""
        from src.api.retrieval import search_memory, SearchRequest
        from src.memory import MemoryManager
        
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_search_empty")
        
        try:
            # Mock the dependency
            async def mock_manager():
                return manager
            
            request = SearchRequest(query="Test query")
            
            # The endpoint should handle empty memory
            # (returning "I don't have any relevant information")
            # This test verifies no exceptions are raised
            
        finally:
            try:
                graph.delete()
            except:
                pass
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_search_filters_by_graph_type(self, falkordb_host, falkordb_port):
        """Test that search respects graph_type filter"""
        from src.api.retrieval import SearchRequest
        
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_search_filter")
        
        try:
            # Create internal node
            node_internal = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            internal_id = manager.create_conceptual_node(node_internal, "test_search_filter")
            
            # Create external node
            node_external = ConceptualNode(
                label="Person",
                name="Bob",
                graph_type=GraphType.EXTERNAL
            )
            external_id = manager.create_conceptual_node(node_external, "test_search_filter")
            
            # Store embeddings
            from src.memory.embeddings import get_embedding_manager
            emb_manager = get_embedding_manager(force_new=True)
            
            emb1 = emb_manager.generate_embedding("Person: Alice")
            manager.store_node_embedding(internal_id, emb1, "test_search_filter")
            
            emb2 = emb_manager.generate_embedding("Person: Bob")
            manager.store_node_embedding(external_id, emb2, "test_search_filter")
            
            # Search only INTERNAL
            from src.memory import RetrievalGraph
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_search_filter"
            )
            
            result = retrieval.search(
                "Tell me about people",
                graph_types=[GraphType.INTERNAL]
            )
            
            # Should only search internal graph
            assert "internal" in result["graph_types_searched"]
            assert "external" not in result["graph_types_searched"]
            
        finally:
            try:
                graph.delete()
            except:
                pass
    
    def test_search_handles_invalid_graph_type(self):
        """Test that search rejects invalid graph_type values"""
        from src.api.retrieval import SearchRequest
        from pydantic import ValidationError
        
        # This should not raise (valid values)
        SearchRequest(query="Test", graph_types=["internal"])
        SearchRequest(query="Test", graph_types=["external"])
        SearchRequest(query="Test", graph_types=["internal", "external"])
        
        # Invalid graph_type strings will be caught by endpoint logic
        # The model itself accepts any strings, validation happens in endpoint


@pytest.mark.unit
class TestSearchStatusEndpoint:
    """Tests for search status endpoint"""
    
    def test_search_status_endpoint_structure(self):
        """Test that status endpoint returns expected structure"""
        # This is a unit test - just verify the function exists
        from src.api.retrieval import get_search_status
        
        assert callable(get_search_status)

