"""
MemoryManager - Main class for managing connections to FalkorDB

This class provides a unified interface for interacting with the graph database,
handling both short-term memory (STM) and long-term memory (LTM).
"""

from typing import Optional
from falkordb import FalkorDB, Graph
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    MemoryManager handles all interactions with FalkorDB.
    
    It provides:
    - Connection management to FalkorDB
    - Graph selection and management
    - Basic CRUD operations for the knowledge graph
    
    Attributes:
        host (str): FalkorDB host address
        port (int): FalkorDB port number
        db (FalkorDB): FalkorDB connection instance
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379):
        """
        Initialize MemoryManager with connection parameters.
        
        Args:
            host: FalkorDB host address (default: localhost)
            port: FalkorDB port number (default: 6379)
        
        Raises:
            ConnectionError: If unable to connect to FalkorDB
        """
        self.host = host
        self.port = port
        
        try:
            self.db = FalkorDB(host=host, port=port)
            logger.info(f"MemoryManager initialized with FalkorDB at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB at {host}:{port}: {e}")
            raise ConnectionError(f"Cannot connect to FalkorDB: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if the connection to FalkorDB is active.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            # Simple health check - try to list graphs
            _ = self.db.list_graphs()
            return True
        except Exception as e:
            logger.warning(f"Connection check failed: {e}")
            return False
    
    def get_graph(self, graph_name: str) -> Graph:
        """
        Get or create a graph by name.
        
        Args:
            graph_name: Name of the graph to access
        
        Returns:
            Graph: FalkorDB Graph instance
        
        Raises:
            RuntimeError: If unable to select graph
        """
        try:
            graph = self.db.select_graph(graph_name)
            logger.debug(f"Selected graph: {graph_name}")
            return graph
        except Exception as e:
            logger.error(f"Failed to select graph {graph_name}: {e}")
            raise RuntimeError(f"Cannot select graph {graph_name}: {e}")
    
    def clear_graph(self, graph_name: str) -> None:
        """
        Clear all nodes and relationships from a graph.
        
        Args:
            graph_name: Name of the graph to clear
        """
        try:
            graph = self.get_graph(graph_name)
            graph.query("MATCH (n) DETACH DELETE n")
            logger.info(f"Cleared graph: {graph_name}")
        except Exception as e:
            logger.error(f"Failed to clear graph {graph_name}: {e}")
            raise RuntimeError(f"Cannot clear graph {graph_name}: {e}")
    
    def delete_graph(self, graph_name: str) -> None:
        """
        Delete a graph completely.
        
        Args:
            graph_name: Name of the graph to delete
        """
        try:
            graph = self.get_graph(graph_name)
            graph.delete()
            logger.info(f"Deleted graph: {graph_name}")
        except Exception as e:
            logger.error(f"Failed to delete graph {graph_name}: {e}")
            raise RuntimeError(f"Cannot delete graph {graph_name}: {e}")
    
    def list_graphs(self) -> list[str]:
        """
        List all available graphs.
        
        Returns:
            list[str]: List of graph names
        """
        try:
            graphs = self.db.list_graphs()
            return graphs
        except Exception as e:
            logger.error(f"Failed to list graphs: {e}")
            return []
    
    def get_graph_stats(self, graph_name: str) -> dict:
        """
        Get statistics about a graph.
        
        Args:
            graph_name: Name of the graph
        
        Returns:
            dict: Statistics including node count, edge count, etc.
        """
        try:
            graph = self.get_graph(graph_name)
            
            # Count nodes
            node_result = graph.query("MATCH (n) RETURN count(n) AS count")
            node_count = node_result.result_set[0][0] if node_result.result_set else 0
            
            # Count relationships
            rel_result = graph.query("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = rel_result.result_set[0][0] if rel_result.result_set else 0
            
            return {
                "graph_name": graph_name,
                "node_count": node_count,
                "relationship_count": rel_count
            }
        except Exception as e:
            logger.error(f"Failed to get stats for graph {graph_name}: {e}")
            return {
                "graph_name": graph_name,
                "node_count": 0,
                "relationship_count": 0,
                "error": str(e)
            }
    
    def __repr__(self) -> str:
        """String representation of MemoryManager"""
        return f"MemoryManager(host='{self.host}', port={self.port})"

