"""
Tests for MemoryManager class

Following TDD approach:
1. Write failing test
2. Implement minimum code to pass
3. Refactor if needed
"""

import pytest
from src.memory.manager import MemoryManager


@pytest.mark.integration
class TestMemoryManagerConnection:
    """Tests for MemoryManager database connection"""
    
    def test_memory_manager_can_be_instantiated(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager can be created with host and port
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        assert manager is not None
        assert manager.host == falkordb_host
        assert manager.port == falkordb_port
    
    def test_memory_manager_connects_to_falkordb(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager successfully connects to FalkorDB
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        
        # Should be able to get a connection
        assert manager.db is not None
        
        # Should be able to check connection health
        is_connected = manager.is_connected()
        assert is_connected is True
    
    def test_memory_manager_can_select_graph(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager can select a graph
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph_name = "test_memory_graph"
        
        graph = manager.get_graph(graph_name)
        assert graph is not None
    
    def test_memory_manager_can_execute_simple_query(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager can execute a simple query
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_simple_query")
        
        # Execute simple query
        result = graph.query("RETURN 'Hello from FalkorDB' AS message")
        
        # Verify result
        assert result is not None
        assert len(result.result_set) > 0
        assert result.result_set[0][0] == "Hello from FalkorDB"
        
        # Cleanup
        graph.delete()
    
    def test_memory_manager_handles_connection_errors(self):
        """
        Test that MemoryManager handles connection errors gracefully
        """
        # Try to connect to non-existent host
        with pytest.raises(Exception):
            manager = MemoryManager(host="nonexistent-host", port=9999)
            manager.is_connected()


@pytest.mark.integration
class TestMemoryManagerGraphOperations:
    """Tests for MemoryManager graph operations"""
    
    def test_memory_manager_can_create_node(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager can create a node in the graph
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_create_node")
        
        # Create a simple node
        result = graph.query("""
            CREATE (n:TestNode {name: 'Test', value: 42})
            RETURN n
        """)
        
        assert result is not None
        
        # Verify node was created
        verify_result = graph.query("MATCH (n:TestNode) RETURN count(n) AS count")
        assert verify_result.result_set[0][0] == 1
        
        # Cleanup
        graph.delete()
    
    def test_memory_manager_can_clear_graph(self, falkordb_host, falkordb_port):
        """
        Test that MemoryManager can clear all nodes from graph
        """
        manager = MemoryManager(host=falkordb_host, port=falkordb_port)
        graph = manager.get_graph("test_clear_graph")
        
        # Create some nodes
        graph.query("CREATE (n:TestNode {id: 1})")
        graph.query("CREATE (n:TestNode {id: 2})")
        
        # Clear graph
        manager.clear_graph("test_clear_graph")
        
        # Verify graph is empty
        result = graph.query("MATCH (n) RETURN count(n) AS count")
        assert result.result_set[0][0] == 0
        
        # Cleanup
        graph.delete()

