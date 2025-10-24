"""
End-to-end integration tests for retrieval workflow.

Tests the complete flow: STM -> Consolidation (with embeddings) -> Vector Search -> Response
"""

import pytest
from src.memory.stm import ShortTermMemoryBuffer, Observation
from src.memory.manager import MemoryManager
from src.memory.consolidation import ConsolidationGraph
from src.memory.retrieval import RetrievalGraph
from src.memory.schema import GraphType
import os

# This test requires a real OpenAI API key
@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY environment variable"
)
class TestFullRetrievalWorkflow:
    """
    End-to-end tests for the full retrieval workflow, from observation to search.
    These tests interact with a live FalkorDB instance and OpenAI API.
    """

    def test_full_workflow_single_observation(self, memory_manager, stm_buffer):
        """
        Tests the full retrieval workflow from observation to search result.
        """
        # 1. Add an observation to STM
        stm_buffer.add_observation("Alice is a Python programmer.")

        # 2. Run consolidation
        consolidation_graph = ConsolidationGraph(
            stm_buffer=stm_buffer, memory_manager=memory_manager
        )
        consolidation_result = consolidation_graph.run()
        assert consolidation_result["status"] == "success"
        assert consolidation_result["nodes_created"] > 0

        # 3. Verify that the STM is cleared
        assert stm_buffer.is_empty()

        # 4. Search for a related concept
        retrieval_graph = RetrievalGraph(memory_manager=memory_manager)
        result = retrieval_graph.search("Who is Alice?")

        # 5. Check if the response is relevant
        assert result["status"] == "success"
        response_lower = result["response"].lower()
        assert "python" in response_lower or "alice" in response_lower

    def test_full_workflow_multiple_observations(self, memory_manager, stm_buffer):
        """
        Tests the full retrieval workflow with multiple observations.
        """
        # 1. Add observations
        stm_buffer.add_observation("Bob works for a company called GenTech.")
        stm_buffer.add_observation("GenTech is located in San Francisco.")

        # 2. Run consolidation
        consolidation_graph = ConsolidationGraph(
            stm_buffer=stm_buffer, memory_manager=memory_manager
        )
        consolidation_graph.run()

        # 3. Search for a related concept
        retrieval_graph = RetrievalGraph(memory_manager=memory_manager)
        result = retrieval_graph.search("Where does Bob work?")

        # 5. Check for relevant response
        assert result["status"] == "success"
        response_lower = result["response"].lower()
        assert "gentech" in response_lower or "san francisco" in response_lower

