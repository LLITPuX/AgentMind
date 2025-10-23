"""
MemoryManager - Main class for managing connections to FalkorDB

This class provides a unified interface for interacting with the graph database,
handling both short-term memory (STM) and long-term memory (LTM).
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from falkordb import FalkorDB, Graph
import logging

from .schema import ConceptualNode, ConceptualEdge, Statement, GraphType

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
    
    # =========================================================================
    # Bitemporal Entity Management (Stage 2)
    # =========================================================================
    
    def create_conceptual_node(
        self,
        node: ConceptualNode,
        graph_name: str = "agentmind_ltm"
    ) -> str:
        """
        Create a ConceptualNode in the graph database.
        
        Args:
            node: ConceptualNode instance to create
            graph_name: Name of the graph to store the node in
        
        Returns:
            str: The ID of the created node
        
        Raises:
            RuntimeError: If node creation fails
        """
        try:
            graph = self.get_graph(graph_name)
            
            # Convert datetime objects to ISO format strings
            valid_from_str = node.valid_from.isoformat()
            valid_until_str = node.valid_until.isoformat()
            tx_time_from_str = node.tx_time_from.isoformat()
            tx_time_to_str = node.tx_time_to.isoformat() if node.tx_time_to else None
            
            # Build Cypher query with parameters
            query = """
            CREATE (n:ConceptualNode {
                id: $id,
                label: $label,
                name: $name,
                graph_type: $graph_type,
                valid_from: $valid_from,
                valid_until: $valid_until,
                tx_time_from: $tx_time_from,
                tx_time_to: $tx_time_to
            })
            RETURN n.id AS id
            """
            
            params = {
                "id": node.id,
                "label": node.label,
                "name": node.name,
                "graph_type": node.graph_type.value,
                "valid_from": valid_from_str,
                "valid_until": valid_until_str,
                "tx_time_from": tx_time_from_str,
                "tx_time_to": tx_time_to_str
            }
            
            # Store properties as JSON if present
            if node.properties:
                # For simplicity, we'll store each property as a separate field
                for key, value in node.properties.items():
                    params[f"prop_{key}"] = str(value)
                    query = query.replace(
                        "tx_time_to: $tx_time_to",
                        f"tx_time_to: $tx_time_to,\n                {key}: $prop_{key}"
                    )
            
            result = graph.query(query, params)
            
            logger.info(f"Created ConceptualNode: {node.id} ({node.label}: {node.name})")
            return node.id
            
        except Exception as e:
            logger.error(f"Failed to create ConceptualNode: {e}")
            raise RuntimeError(f"Cannot create ConceptualNode: {e}")
    
    def create_conceptual_edge(
        self,
        edge: ConceptualEdge,
        graph_name: str = "agentmind_ltm"
    ) -> str:
        """
        Create a ConceptualEdge in the graph database.
        
        Args:
            edge: ConceptualEdge instance to create
            graph_name: Name of the graph to store the edge in
        
        Returns:
            str: The ID of the created edge
        
        Raises:
            RuntimeError: If edge creation fails
        """
        try:
            graph = self.get_graph(graph_name)
            
            # Convert datetime objects to ISO format strings
            valid_from_str = edge.valid_from.isoformat()
            valid_until_str = edge.valid_until.isoformat()
            tx_time_from_str = edge.tx_time_from.isoformat()
            tx_time_to_str = edge.tx_time_to.isoformat() if edge.tx_time_to else None
            
            # Build Cypher query
            query = """
            MATCH (from:ConceptualNode {id: $from_node_id})
            MATCH (to:ConceptualNode {id: $to_node_id})
            CREATE (from)-[r:CONCEPTUAL_EDGE {
                id: $id,
                edge_type: $edge_type,
                graph_type: $graph_type,
                valid_from: $valid_from,
                valid_until: $valid_until,
                tx_time_from: $tx_time_from,
                tx_time_to: $tx_time_to
            }]->(to)
            RETURN r.id AS id
            """
            
            params = {
                "id": edge.id,
                "edge_type": edge.edge_type,
                "from_node_id": edge.from_node_id,
                "to_node_id": edge.to_node_id,
                "graph_type": edge.graph_type.value,
                "valid_from": valid_from_str,
                "valid_until": valid_until_str,
                "tx_time_from": tx_time_from_str,
                "tx_time_to": tx_time_to_str
            }
            
            # Add properties if present
            if edge.properties:
                for key, value in edge.properties.items():
                    params[f"prop_{key}"] = str(value)
                    query = query.replace(
                        "tx_time_to: $tx_time_to",
                        f"tx_time_to: $tx_time_to,\n                {key}: $prop_{key}"
                    )
            
            result = graph.query(query, params)
            
            logger.info(f"Created ConceptualEdge: {edge.id} ({edge.edge_type})")
            return edge.id
            
        except Exception as e:
            logger.error(f"Failed to create ConceptualEdge: {e}")
            raise RuntimeError(f"Cannot create ConceptualEdge: {e}")
    
    def create_statement(
        self,
        stmt: Statement,
        graph_name: str = "agentmind_ltm"
    ) -> str:
        """
        Create a Statement node in the graph database.
        
        Statements are claims about ConceptualNodes or ConceptualEdges.
        
        Args:
            stmt: Statement instance to create
            graph_name: Name of the graph to store the statement in
        
        Returns:
            str: The ID of the created statement
        
        Raises:
            RuntimeError: If statement creation fails
        """
        try:
            graph = self.get_graph(graph_name)
            
            # Convert datetime objects to ISO format strings
            valid_from_str = stmt.valid_from.isoformat()
            valid_until_str = stmt.valid_until.isoformat()
            tx_time_from_str = stmt.tx_time_from.isoformat()
            tx_time_to_str = stmt.tx_time_to.isoformat() if stmt.tx_time_to else None
            
            # Build Cypher query
            query = """
            CREATE (s:Statement {
                id: $id,
                asserts_about_conceptual_id: $asserts_about_conceptual_id,
                source_name: $source_name,
                source_type: $source_type,
                source_reliability: $source_reliability,
                confidence: $confidence,
                valid_from: $valid_from,
                valid_until: $valid_until,
                tx_time_from: $tx_time_from,
                tx_time_to: $tx_time_to
            })
            RETURN s.id AS id
            """
            
            params = {
                "id": stmt.id,
                "asserts_about_conceptual_id": stmt.asserts_about_conceptual_id,
                "source_name": stmt.source.name,
                "source_type": stmt.source.type.value,
                "source_reliability": stmt.source.reliability_score,
                "confidence": stmt.confidence,
                "valid_from": valid_from_str,
                "valid_until": valid_until_str,
                "tx_time_from": tx_time_from_str,
                "tx_time_to": tx_time_to_str
            }
            
            # Add attributes if present
            if stmt.attributes:
                for key, value in stmt.attributes.items():
                    params[f"attr_{key}"] = str(value)
                    query = query.replace(
                        "tx_time_to: $tx_time_to",
                        f"tx_time_to: $tx_time_to,\n                attr_{key}: $attr_{key}"
                    )
            
            result = graph.query(query, params)
            
            # Create relationship to the concept it's about
            link_query = """
            MATCH (s:Statement {id: $stmt_id})
            MATCH (c) WHERE c.id = $concept_id
            CREATE (s)-[:ASSERTS_ABOUT]->(c)
            """
            
            graph.query(link_query, {
                "stmt_id": stmt.id,
                "concept_id": stmt.asserts_about_conceptual_id
            })
            
            logger.info(f"Created Statement: {stmt.id} (about: {stmt.asserts_about_conceptual_id})")
            return stmt.id
            
        except Exception as e:
            logger.error(f"Failed to create Statement: {e}")
            raise RuntimeError(f"Cannot create Statement: {e}")
    
    def expire_node(
        self,
        node_id: str,
        tx_time_to: datetime,
        graph_name: str = "agentmind_ltm"
    ) -> None:
        """
        Mark a ConceptualNode as expired by setting its tx_time_to.
        
        This doesn't delete the node, but marks it as no longer current.
        
        Args:
            node_id: ID of the node to expire
            tx_time_to: When this record was superseded
            graph_name: Name of the graph
        
        Raises:
            RuntimeError: If update fails
        """
        try:
            graph = self.get_graph(graph_name)
            
            query = """
            MATCH (n:ConceptualNode {id: $node_id})
            SET n.tx_time_to = $tx_time_to
            RETURN n.id AS id
            """
            
            result = graph.query(query, {
                "node_id": node_id,
                "tx_time_to": tx_time_to.isoformat()
            })
            
            if not result.result_set:
                raise RuntimeError(f"Node with id {node_id} not found")
            
            logger.info(f"Expired ConceptualNode: {node_id} at {tx_time_to}")
            
        except Exception as e:
            logger.error(f"Failed to expire node: {e}")
            raise RuntimeError(f"Cannot expire node: {e}")
    
    def expire_edge(
        self,
        edge_id: str,
        tx_time_to: datetime,
        graph_name: str = "agentmind_ltm"
    ) -> None:
        """
        Mark a ConceptualEdge as expired by setting its tx_time_to.
        
        Args:
            edge_id: ID of the edge to expire
            tx_time_to: When this record was superseded
            graph_name: Name of the graph
        
        Raises:
            RuntimeError: If update fails
        """
        try:
            graph = self.get_graph(graph_name)
            
            query = """
            MATCH ()-[r:CONCEPTUAL_EDGE {id: $edge_id}]->()
            SET r.tx_time_to = $tx_time_to
            RETURN r.id AS id
            """
            
            result = graph.query(query, {
                "edge_id": edge_id,
                "tx_time_to": tx_time_to.isoformat()
            })
            
            if not result.result_set:
                raise RuntimeError(f"Edge with id {edge_id} not found")
            
            logger.info(f"Expired ConceptualEdge: {edge_id} at {tx_time_to}")
            
        except Exception as e:
            logger.error(f"Failed to expire edge: {e}")
            raise RuntimeError(f"Cannot expire edge: {e}")
    
    def query_nodes_at_time(
        self,
        label: str,
        valid_time: datetime,
        tx_time: datetime,
        graph_type: Optional[GraphType] = None,
        graph_name: str = "agentmind_ltm"
    ) -> List[Dict[str, Any]]:
        """
        Query ConceptualNodes that were valid at a specific point in time.
        
        This implements bitemporal querying:
        - valid_time: What was true in reality at this time?
        - tx_time: What did we know at this time?
        
        Args:
            label: Node label to filter by
            valid_time: Point in valid time
            tx_time: Point in transaction time
            graph_type: Optional filter by graph_type (internal/external)
            graph_name: Name of the graph
        
        Returns:
            List of node dictionaries
        """
        try:
            graph = self.get_graph(graph_name)
            
            # Build query with bitemporal filters
            query = """
            MATCH (n:ConceptualNode)
            WHERE n.label = $label
              AND n.valid_from <= $valid_time
              AND n.valid_until >= $valid_time
              AND n.tx_time_from <= $tx_time
              AND (n.tx_time_to IS NULL OR n.tx_time_to >= $tx_time)
            """
            
            params = {
                "label": label,
                "valid_time": valid_time.isoformat(),
                "tx_time": tx_time.isoformat()
            }
            
            if graph_type:
                query += " AND n.graph_type = $graph_type"
                params["graph_type"] = graph_type.value
            
            query += " RETURN n"
            
            result = graph.query(query, params)
            
            # Convert result to list of dicts
            nodes = []
            for row in result.result_set:
                node = row[0]
                # FalkorDB returns Node objects with a .properties attribute
                if hasattr(node, 'properties'):
                    nodes.append(node.properties)
                else:
                    nodes.append(node.__dict__ if hasattr(node, '__dict__') else {})
            
            logger.debug(f"Found {len(nodes)} nodes for label '{label}' at valid_time={valid_time}, tx_time={tx_time}")
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to query nodes at time: {e}")
            return []
    
    def get_statements_for_concept(
        self,
        conceptual_id: str,
        graph_name: str = "agentmind_ltm"
    ) -> List[Dict[str, Any]]:
        """
        Get all Statements about a specific ConceptualNode or ConceptualEdge.
        
        This enables multi-source truth: multiple claims about the same entity.
        
        Args:
            conceptual_id: ID of the ConceptualNode or ConceptualEdge
            graph_name: Name of the graph
        
        Returns:
            List of statement dictionaries
        """
        try:
            graph = self.get_graph(graph_name)
            
            query = """
            MATCH (s:Statement)
            WHERE s.asserts_about_conceptual_id = $conceptual_id
            RETURN s
            """
            
            result = graph.query(query, {"conceptual_id": conceptual_id})
            
            # Convert result to list of dicts
            statements = []
            for row in result.result_set:
                stmt = row[0]
                # FalkorDB returns Node objects with a .properties attribute
                if hasattr(stmt, 'properties'):
                    statements.append(stmt.properties)
                else:
                    statements.append(stmt.__dict__ if hasattr(stmt, '__dict__') else {})
            
            logger.debug(f"Found {len(statements)} statements for concept {conceptual_id}")
            return statements
            
        except Exception as e:
            logger.error(f"Failed to get statements: {e}")
            return []

