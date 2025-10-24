import pytest
from unittest.mock import MagicMock, patch
from src.engine import CognitiveEngine

@pytest.fixture
def mock_dependencies():
    """Mocks all external dependencies for CognitiveEngine."""
    with patch('src.engine.MemoryManager') as MockMemoryManager, \
         patch('src.engine.ShortTermMemoryBuffer') as MockStmBuffer, \
         patch('src.engine.ConsolidationGraph') as MockConsolidationGraph, \
         patch('src.engine.RetrievalGraph') as MockRetrievalGraph:
        
        mock_memory_manager = MockMemoryManager.return_value
        mock_stm_buffer = MockStmBuffer.return_value
        mock_consolidation_graph = MockConsolidationGraph.return_value
        mock_retrieval_graph = MockRetrievalGraph.return_value

        yield {
            "memory_manager": mock_memory_manager,
            "stm_buffer": mock_stm_buffer,
            "consolidation_graph": mock_consolidation_graph,
            "retrieval_graph": mock_retrieval_graph,
        }

@pytest.fixture
def cognitive_engine(mock_dependencies):
    """Provides a CognitiveEngine instance with mocked dependencies."""
    # Since __init__ is patched, we can instantiate without side effects
    engine = CognitiveEngine() 
    # Manually assign mocks if needed, or rely on the patch context
    engine.memory_manager = mock_dependencies["memory_manager"]
    engine.stm_buffer = mock_dependencies["stm_buffer"]
    engine.consolidation_graph = mock_dependencies["consolidation_graph"]
    engine.retrieval_graph = mock_dependencies["retrieval_graph"]
    return engine

def test_add_observation(cognitive_engine, mock_dependencies):
    """Tests adding an observation to the STM buffer."""
    observation = "Test observation"
    mock_dependencies["stm_buffer"].add_observation.return_value = 1
    
    result = cognitive_engine.add_observation(observation)
    
    mock_dependencies["stm_buffer"].add_observation.assert_called_once_with(observation)
    assert result == 1

def test_consolidate_memory(cognitive_engine, mock_dependencies):
    """Tests the memory consolidation process."""
    mock_result = {"status": "success"}
    mock_dependencies["consolidation_graph"].run.return_value = mock_result
    
    result = cognitive_engine.consolidate_memory()
    
    mock_dependencies["consolidation_graph"].run.assert_called_once()
    assert result == mock_result

def test_search_memory(cognitive_engine, mock_dependencies):
    """Tests searching the long-term memory."""
    query = "What is the test?"
    mock_search_result = {"status": "success", "response": "This is a test."}
    mock_dependencies["retrieval_graph"].search.return_value = mock_search_result
    
    result = cognitive_engine.search_memory(query=query, top_k=10)
    
    assert cognitive_engine.retrieval_graph.top_k == 10
    mock_dependencies["retrieval_graph"].search.assert_called_once_with(
        query=query, graph_types=None
    )
    assert result == mock_search_result

def test_get_full_graph(cognitive_engine, mock_dependencies):
    """Tests retrieving the full knowledge graph."""
    mock_graph = {"nodes": [], "links": []}
    mock_dependencies["memory_manager"].get_full_graph.return_value = mock_graph
    
    result = cognitive_engine.get_full_graph()
    
    mock_dependencies["memory_manager"].get_full_graph.assert_called_once()
    assert result == mock_graph

def test_get_stm_status(cognitive_engine, mock_dependencies):
    """Tests retrieving the STM status."""
    mock_dependencies["stm_buffer"].size.return_value = 5
    mock_dependencies["stm_buffer"].is_empty.return_value = False

    status = cognitive_engine.get_stm_status()

    assert status["stm_size"] == 5
    assert status["is_empty"] is False
    assert status["ready_for_consolidation"] is True
    mock_dependencies["stm_buffer"].size.assert_called_once()
    mock_dependencies["stm_buffer"].is_empty.assert_called_once()
