"""
End-to-end integration tests for retrieval workflow.

Tests the complete flow: STM -> Consolidation (with embeddings) -> Vector Search -> Response
"""

import pytest
from datetime import datetime
import os

from src.memory import (
    ShortTermMemoryBuffer,
    MemoryManager,
    Observation,
    ConsolidationGraph,
    RetrievalGraph,
    GraphType
)


@pytest.mark.integration
class TestFullRetrievalWorkflow:
    """E2E tests for complete memory consolidation and retrieval"""
    
    @pytest.fixture
    def setup_clean_memory(self, falkordb_host, falkordb_port):
        """Setup clean STM and LTM for testing"""
        stm = ShortTermMemoryBuffer(
            host=falkordb_host,
            port=falkordb_port,
            buffer_key="test_e2e_retrieval_stm"
        )
        
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        
        # Clear STM and graph
        stm.clear()
        try:
            manager.clear_graph("test_e2e_retrieval_ltm")
        except:
            pass
        
        yield stm, manager
        
        # Cleanup
        stm.clear()
        try:
            manager.delete_graph("test_e2e_retrieval_ltm")
        except:
            pass
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_full_workflow_single_observation(self, setup_clean_memory):
        """
        E2E test: Add observation -> Consolidate -> Search -> Get response
        
        This test verifies the complete flow works end-to-end.
        """
        stm, manager = setup_clean_memory
        
        # Step 1: Add observation to STM
        stm.add(Observation(
            content="Alice likes Python programming",
            timestamp=datetime.now(),
            metadata={"source": "user_chat"}
        ))
        
        # Verify observation is in STM
        assert stm.size() == 1
        
        # Step 2: Consolidate (extracts entities, stores in LTM with embeddings)
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        # Override graph_name for consolidation
        consolidation.memory_manager = manager
        result = consolidation.run()
        
        # Verify consolidation succeeded
        assert result["status"] == "completed"
        assert result["observations_processed"] == 1
        
        # STM should be cleared after consolidation
        assert stm.is_empty()
        
        # Step 3: Search memory
        retrieval = RetrievalGraph(
            memory_manager=manager,
            graph_name="agentmind_ltm"  # Consolidation uses default graph
        )
        
        search_result = retrieval.search("What does Alice like?")
        
        # Verify search succeeded
        assert search_result["status"] == "completed"
        assert search_result["response"] is not None
        
        # Response should mention Python or Alice
        response_lower = search_result["response"].lower()
        assert "python" in response_lower or "alice" in response_lower
        
        # Should have found sources
        assert search_result["metadata"]["sources_count"] > 0
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_full_workflow_multiple_observations(self, setup_clean_memory):
        """
        E2E test with multiple related observations.
        """
        stm, manager = setup_clean_memory
        
        # Add multiple observations
        observations = [
            "Alice likes Python programming",
            "Bob prefers JavaScript",
            "Alice works at Google"
        ]
        
        for obs_text in observations:
            stm.add(Observation(
                content=obs_text,
                timestamp=datetime.now(),
                metadata={"source": "chat"}
            ))
        
        assert stm.size() == 3
        
        # Consolidate
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        result = consolidation.run()
        
        assert result["status"] == "completed"
        assert result["observations_processed"] == 3
        
        # Search for Alice-specific info
        retrieval = RetrievalGraph(
            memory_manager=manager,
            graph_name="agentmind_ltm"
        )
        
        search_result = retrieval.search("What do you know about Alice?")
        
        assert search_result["status"] == "completed"
        response_lower = search_result["response"].lower()
        
        # Should mention Alice
        assert "alice" in response_lower
        # Should have found some sources (even if not all details extracted)
        assert search_result["metadata"]["sources_count"] >= 1
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_search_filters_by_graph_type(self, setup_clean_memory):
        """
        E2E test: Verify search can filter by graph_type
        """
        stm, manager = setup_clean_memory
        
        # Add observation that should create INTERNAL entities
        stm.add(Observation(
            content="I prefer dark mode in my IDE",
            timestamp=datetime.now()
        ))
        
        # Consolidate
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        consolidation.run()
        
        # Search only INTERNAL graph
        retrieval = RetrievalGraph(
            memory_manager=manager,
            graph_name="agentmind_ltm"
        )
        
        result = retrieval.search(
            "What are my preferences?",
            graph_types=[GraphType.INTERNAL]
        )
        
        assert result["status"] == "completed"
        assert "internal" in result["graph_types_searched"]
        assert "external" not in result["graph_types_searched"]
    
    def test_search_with_empty_memory_returns_appropriate_response(self, setup_clean_memory):
        """
        E2E test: Search on empty memory returns appropriate message
        """
        stm, manager = setup_clean_memory
        
        # Don't add any observations - memory is empty
        
        retrieval = RetrievalGraph(
            memory_manager=manager,
            graph_name="test_e2e_retrieval_ltm"
        )
        
        result = retrieval.search("What do you know about anything?")
        
        # Should still complete successfully
        assert result["status"] == "completed"
        
        # Should indicate no information available
        response_lower = result["response"].lower()
        assert "don't have" in response_lower or "no information" in response_lower or "not have" in response_lower
        
        # Should have zero sources
        assert result["metadata"]["sources_count"] == 0
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_consolidated_embeddings_are_searchable(self, setup_clean_memory):
        """
        E2E test: Verify that embeddings created during consolidation are searchable
        """
        stm, manager = setup_clean_memory
        
        # Add observation
        stm.add(Observation(
            content="Python is a popular programming language",
            timestamp=datetime.now()
        ))
        
        # Consolidate
        consolidation = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        result = consolidation.run()
        
        assert result["status"] == "completed"
        
        # Now search using semantically similar query
        retrieval = RetrievalGraph(
            memory_manager=manager,
            graph_name="agentmind_ltm"
        )
        
        # Use different wording but same semantic meaning
        search_result = retrieval.search("Tell me about programming languages")
        
        # Should find Python through vector similarity
        assert search_result["status"] == "completed"
        assert "python" in search_result["response"].lower()

