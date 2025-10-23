"""
Unit tests for RetrievalGraph.

Tests the retrieval graph structure and individual nodes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from datetime import datetime

from src.memory import (
    RetrievalGraph,
    MemoryManager,
    ConceptualNode,
    GraphType
)


@pytest.mark.unit
class TestRetrievalGraphStructure:
    """Tests for RetrievalGraph structure"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_retrieval_graph_can_be_created(self):
        """Test that RetrievalGraph can be instantiated"""
        manager = Mock(spec=MemoryManager)
        
        # Should not raise
        graph = RetrievalGraph(memory_manager=manager)
        
        assert graph is not None
        assert graph.memory_manager == manager
        assert graph.top_k == 5  # Default value
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_retrieval_graph_has_compiled_graph(self):
        """Test that graph is compiled on initialization"""
        manager = Mock(spec=MemoryManager)
        
        graph = RetrievalGraph(memory_manager=manager)
        
        assert graph.graph is not None
        # LangGraph compiled graph should be callable
        assert callable(graph.graph.invoke)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_retrieval_graph_respects_top_k_parameter(self):
        """Test that top_k parameter is set correctly"""
        manager = Mock(spec=MemoryManager)
        
        graph = RetrievalGraph(memory_manager=manager, top_k=10)
        
        assert graph.top_k == 10


@pytest.mark.integration
class TestRetrievalGraphNodes:
    """Tests for individual nodes in retrieval workflow"""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_vector_search_node_generates_embedding(self, falkordb_host, falkordb_port):
        """Test that vector_search_node generates query embedding"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_retrieval_search")
        
        try:
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_retrieval_search"
            )
            
            state = {
                "query": "Test query",
                "graph_types": [GraphType.INTERNAL],
                "messages": []
            }
            
            result = retrieval.vector_search_node(state)
            
            # Should have query_embedding
            assert "query_embedding" in result
            assert len(result["query_embedding"]) > 0
            # Should have vector_results (even if empty)
            assert "vector_results" in result
            
        finally:
            try:
                graph.delete()
            except:
                pass
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_vector_search_node_finds_relevant_nodes(self, falkordb_host, falkordb_port):
        """Test that vector_search_node finds nodes with similar embeddings"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_retrieval_find")
        
        try:
            # Create a node with embedding
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL,
                properties={"likes": "Python"}
            )
            node_id = manager.create_conceptual_node(node, "test_retrieval_find")
            
            # Store embedding
            from src.memory.embeddings import get_embedding_manager
            emb_manager = get_embedding_manager(force_new=True)
            text_embedding = emb_manager.generate_embedding("Person: Alice. likes: Python")
            manager.store_node_embedding(node_id, text_embedding, "test_retrieval_find")
            
            # Create retrieval graph
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_retrieval_find"
            )
            
            state = {
                "query": "Who likes Python?",
                "graph_types": [GraphType.INTERNAL],
                "messages": []
            }
            
            result = retrieval.vector_search_node(state)
            
            # Should find the node
            assert len(result["vector_results"]) >= 1
            # Alice should be in results
            result_names = [r['name'] for r in result["vector_results"]]
            assert 'Alice' in result_names
            
        finally:
            try:
                graph.delete()
            except:
                pass
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_graph_expansion_includes_neighbors(self, falkordb_host, falkordb_port):
        """Test that graph_expansion_node expands to neighbors"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph_db = manager.get_graph("test_retrieval_expand")
        
        try:
            # Create two connected nodes
            from src.memory import ConceptualEdge
            
            node1 = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            node1_id = manager.create_conceptual_node(node1, "test_retrieval_expand")
            
            node2 = ConceptualNode(
                label="Language",
                name="Python",
                graph_type=GraphType.EXTERNAL
            )
            node2_id = manager.create_conceptual_node(node2, "test_retrieval_expand")
            
            # Create edge
            edge = ConceptualEdge(
                edge_type="LIKES",
                from_node_id=node1_id,
                to_node_id=node2_id,
                graph_type=GraphType.INTERNAL
            )
            manager.create_conceptual_edge(edge, "test_retrieval_expand")
            
            # Create retrieval graph
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_retrieval_expand"
            )
            
            state = {
                "vector_results": [
                    {"id": node1_id, "name": "Alice", "label": "Person"}
                ],
                "messages": []
            }
            
            result = retrieval.graph_expansion_node(state)
            
            # Should have expanded subgraph
            assert "expanded_subgraph" in result
            subgraph = result["expanded_subgraph"]
            
            # Should include both nodes
            assert len(subgraph["nodes"]) >= 2
            node_names = [n['name'] for n in subgraph["nodes"]]
            assert 'Alice' in node_names
            assert 'Python' in node_names
            
            # Should include edge
            assert len(subgraph["edges"]) >= 1
            
        finally:
            graph_db.delete()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_graph_expansion_includes_statements(self, falkordb_host, falkordb_port):
        """Test that graph_expansion_node includes statements"""
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph_db = manager.get_graph("test_retrieval_stmt")
        
        try:
            from src.memory import Statement, Source, SourceType
            
            # Create node
            node = ConceptualNode(
                label="Person",
                name="Alice",
                graph_type=GraphType.INTERNAL
            )
            node_id = manager.create_conceptual_node(node, "test_retrieval_stmt")
            
            # Create statement about node
            source = Source(name="User_001", type=SourceType.USER)
            stmt = Statement(
                asserts_about_conceptual_id=node_id,
                source=source,
                attributes={"likes": "Python"},
                confidence=0.9
            )
            manager.create_statement(stmt, "test_retrieval_stmt")
            
            # Create retrieval graph
            retrieval = RetrievalGraph(
                memory_manager=manager,
                graph_name="test_retrieval_stmt"
            )
            
            state = {
                "vector_results": [
                    {"id": node_id, "name": "Alice", "label": "Person"}
                ],
                "messages": []
            }
            
            result = retrieval.graph_expansion_node(state)
            
            # Should have statements
            subgraph = result["expanded_subgraph"]
            assert len(subgraph["statements"]) >= 1
            
        finally:
            graph_db.delete()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    @patch('src.memory.retrieval.ChatOpenAI')
    def test_response_synthesis_generates_text_response(self, mock_llm_class):
        """Test that response_synthesis_node generates a text response"""
        # Mock LLM response
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Alice likes Python programming."
        mock_llm.invoke.return_value = mock_response
        mock_llm_class.return_value = mock_llm
        
        manager = Mock(spec=MemoryManager)
        
        retrieval = RetrievalGraph(memory_manager=manager)
        
        state = {
            "query": "What does Alice like?",
            "expanded_subgraph": {
                "nodes": [
                    {"id": "1", "name": "Alice", "label": "Person", "graph_type": "internal"}
                ],
                "edges": [],
                "statements": [
                    {"source_name": "User_001", "attributes": {"likes": "Python"}, "confidence": 0.9}
                ]
            },
            "messages": []
        }
        
        result = retrieval.response_synthesis_node(state)
        
        # Should have response
        assert "response" in result
        assert result["response"] == "Alice likes Python programming."
        # Should have metadata
        assert "metadata" in result
        assert result["metadata"]["sources_count"] >= 1

