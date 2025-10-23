"""
Pytest configuration and fixtures for AgentMind tests
"""

import pytest
import os
from falkordb import FalkorDB


@pytest.fixture(scope="session")
def falkordb_host():
    """FalkorDB host from environment or default"""
    return os.getenv("FALKORDB_HOST", "localhost")


@pytest.fixture(scope="session")
def falkordb_port():
    """FalkorDB port from environment or default"""
    return int(os.getenv("FALKORDB_PORT", 6379))


@pytest.fixture(scope="function")
def falkordb_connection(falkordb_host, falkordb_port):
    """
    Provides a FalkorDB connection for each test.
    Yields the database instance.
    """
    db = FalkorDB(host=falkordb_host, port=falkordb_port)
    yield db
    # Cleanup happens in individual tests if needed


@pytest.fixture(scope="function")
def test_graph(falkordb_connection):
    """
    Provides a clean test graph for each test.
    Automatically cleans up after the test.
    """
    graph_name = "test_memory_graph"
    graph = falkordb_connection.select_graph(graph_name)
    
    # Clean graph before test
    try:
        graph.query("MATCH (n) DETACH DELETE n")
    except:
        pass
    
    yield graph
    
    # Clean graph after test
    try:
        graph.delete()
    except:
        pass

