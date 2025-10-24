import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the app object from main
from src.main import app

# Now, we patch the engine created in the dependencies module
@pytest.fixture(autouse=True)
def mock_engine():
    """Mocks the CognitiveEngine for all tests in this module."""
    with patch('src.dependencies.engine', autospec=True) as mock_engine_instance:
        yield mock_engine_instance

@pytest.fixture
def client():
    """Provides a TestClient for the FastAPI app."""
    return TestClient(app)

def test_get_full_graph_success(client, mock_engine):
    """Tests the GET /api/graph/full endpoint for a successful response."""
    mock_graph_data = {"nodes": [{"id": 1}], "links": []}
    mock_engine.get_full_graph.return_value = mock_graph_data
    
    response = client.get("/api/graph/full")
    
    assert response.status_code == 200
    assert response.json() == mock_graph_data
    mock_engine.get_full_graph.assert_called_once()

def test_get_full_graph_exception(client, mock_engine):
    """Tests the GET /api/graph/full endpoint when the engine raises an exception."""
    mock_engine.get_full_graph.side_effect = Exception("Database error")
    
    response = client.get("/api/graph/full")
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Database error"}

def test_add_observation_success(client, mock_engine):
    """Tests the POST /api/observations endpoint for a successful response."""
    mock_engine.add_observation.return_value = 5
    
    response = client.post("/api/observations", json={"observation": "A new fact"})
    
    assert response.status_code == 200
    assert response.json() == {"status": "success", "stm_size": 5}
    mock_engine.add_observation.assert_called_once_with("A new fact")

def test_add_observation_empty(client, mock_engine):
    """Tests the POST /api/observations endpoint with an empty observation."""
    response = client.post("/api/observations", json={"observation": "  "})
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Observation cannot be empty."}
    mock_engine.add_observation.assert_not_called()

def test_add_observation_exception(client, mock_engine):
    """Tests the POST /api/observations endpoint when the engine raises an exception."""
    mock_engine.add_observation.side_effect = Exception("Redis error")
    
    response = client.post("/api/observations", json={"observation": "A new fact"})
    
    assert response.status_code == 500
    assert response.json() == {"detail": "Redis error"}
