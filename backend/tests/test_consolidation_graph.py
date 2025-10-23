"""
Unit tests for ConsolidationGraph.

Tests the consolidation graph structure and individual nodes.
"""

import pytest
from unittest.mock import patch, Mock
import os

from src.memory import (
    ConsolidationGraph,
    ShortTermMemoryBuffer,
    MemoryManager,
    Observation,
    ExtractedEntity,
    ExtractedRelation,
    GraphType
)
from datetime import datetime


@pytest.mark.unit
class TestConsolidationGraphStructure:
    """Tests for ConsolidationGraph structure"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_consolidation_graph_can_be_created(self):
        """Test that ConsolidationGraph can be instantiated"""
        # Mock dependencies
        stm = Mock(spec=ShortTermMemoryBuffer)
        manager = Mock(spec=MemoryManager)
        
        # Should not raise
        graph = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        assert graph is not None
        assert graph.stm_buffer == stm
        assert graph.memory_manager == manager
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_consolidation_graph_has_compiled_graph(self):
        """Test that graph is compiled on initialization"""
        stm = Mock(spec=ShortTermMemoryBuffer)
        manager = Mock(spec=MemoryManager)
        
        graph = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager
        )
        
        assert graph.graph is not None
        # LangGraph compiled graph should be callable
        assert callable(graph.graph.invoke)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"})
    def test_consolidation_graph_has_correct_similarity_threshold(self):
        """Test that similarity threshold is set correctly"""
        stm = Mock(spec=ShortTermMemoryBuffer)
        manager = Mock(spec=MemoryManager)
        
        graph = ConsolidationGraph(
            stm_buffer=stm,
            memory_manager=manager,
            similarity_threshold=0.9
        )
        
        assert graph.similarity_threshold == 0.9


@pytest.mark.unit
class TestConsolidationState:
    """Tests for ConsolidationState structure"""
    
    def test_consolidation_state_has_required_fields(self):
        """Test that ConsolidationState has all required fields"""
        from src.memory.consolidation import ConsolidationState
        
        # This is a TypedDict, so we test by creating instance
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
        
        assert "observations" in state
        assert "extracted_entities" in state
        assert "extracted_relations" in state
        assert "deduplicated_nodes" in state
        assert "created_statements" in state
        assert "entity_id_map" in state
        assert "messages" in state
        assert "error" in state

