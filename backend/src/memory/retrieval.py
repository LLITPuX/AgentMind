"""
Retrieval Graph - LangGraph agent for hybrid memory search.

Combines vector similarity search with graph expansion to retrieve
relevant context from LTM, then synthesizes a response using LLM.
"""

from typing import TypedDict, List, Annotated, Optional, Dict, Any
import operator
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .manager import MemoryManager
from .schema import GraphType
from .embeddings import get_embedding_manager

logger = logging.getLogger(__name__)


class RetrievalState(TypedDict):
    """
    State for the retrieval workflow.
    
    Tracks the progress of searching memory and generating a response.
    """
    query: str  # User query
    query_embedding: List[float]  # Query vector
    graph_types: List[GraphType]  # Which graphs to search (internal/external)
    vector_results: List[Dict[str, Any]]  # Vector search results
    expanded_subgraph: Dict[str, Any]  # Graph expansion results
    response: str  # Synthesized response
    metadata: Dict[str, Any]  # Additional info (sources, confidence, etc.)
    messages: Annotated[List[BaseMessage], operator.add]  # LLM conversation history
    error: Optional[str]  # Error message if any step fails


class RetrievalGraph:
    """
    LangGraph agent for hybrid retrieval from LTM.
    
    Workflow:
    1. vector_search - Find similar nodes using embeddings
    2. graph_expansion - Expand nodes with neighbors and statements
    3. response_synthesis - Use LLM to generate response from context
    """
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        llm_model: str = "gpt-4o-mini",
        top_k: int = 5,
        graph_name: str = "agentmind_ltm",
        embedding_manager=None
    ):
        """
        Initialize RetrievalGraph.
        
        Args:
            memory_manager: MemoryManager instance
            llm_model: OpenAI model to use for response synthesis
            top_k: Number of top vector search results
            graph_name: Name of the graph to search
            embedding_manager: Optional EmbeddingManager instance (creates new if None)
        """
        self.memory_manager = memory_manager
        self.top_k = top_k
        self.graph_name = graph_name
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0  # Deterministic for retrieval
        )
        
        # Initialize embedding manager
        if embedding_manager is None:
            self.embedding_manager = get_embedding_manager(force_new=True)
        else:
            self.embedding_manager = embedding_manager
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"RetrievalGraph initialized with model: {llm_model}")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(RetrievalState)
        
        # Add nodes
        workflow.add_node("vector_search", self.vector_search_node)
        workflow.add_node("graph_expansion", self.graph_expansion_node)
        workflow.add_node("response_synthesis", self.response_synthesis_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("vector_search")
        workflow.add_edge("vector_search", "graph_expansion")
        workflow.add_edge("graph_expansion", "response_synthesis")
        workflow.add_edge("response_synthesis", END)
        
        return workflow.compile()
    
    def vector_search_node(self, state: RetrievalState) -> RetrievalState:
        """
        Generate query embedding and search for similar nodes.
        
        Args:
            state: Current retrieval state
        
        Returns:
            Updated state with vector search results
        """
        try:
            query = state.get("query", "")
            graph_types = state.get("graph_types", [GraphType.INTERNAL, GraphType.EXTERNAL])
            
            # Generate embedding for query
            query_embedding = self.embedding_manager.generate_embedding(query)
            logger.info(f"Generated query embedding for: '{query}'")
            
            # Search in each graph type
            all_results = []
            for graph_type in graph_types:
                results = self.memory_manager.vector_search_nodes(
                    query_embedding,
                    top_k=self.top_k,
                    graph_type=graph_type,
                    graph_name=self.graph_name
                )
                all_results.extend(results)
                logger.debug(f"Found {len(results)} results in {graph_type.value} graph")
            
            # Sort by similarity score (descending) and take top_k
            all_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            top_results = all_results[:self.top_k]
            
            logger.info(f"Vector search found {len(top_results)} relevant nodes")
            
            return {
                **state,
                "query_embedding": query_embedding,
                "vector_results": top_results,
                "messages": state.get("messages", []) + [
                    SystemMessage(content=f"Vector search found {len(top_results)} relevant nodes")
                ]
            }
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {
                **state,
                "error": f"Vector search failed: {str(e)}",
                "vector_results": []
            }
    
    def graph_expansion_node(self, state: RetrievalState) -> RetrievalState:
        """
        Expand found nodes with 1-hop neighbors and statements.
        
        Args:
            state: Current retrieval state
        
        Returns:
            Updated state with expanded subgraph
        """
        try:
            vector_results = state.get("vector_results", [])
            
            if not vector_results:
                logger.warning("No vector results to expand")
                return {
                    **state,
                    "expanded_subgraph": {"nodes": [], "edges": [], "statements": []}
                }
            
            graph = self.memory_manager.get_graph(self.graph_name)
            
            nodes = []
            edges = []
            statements = []
            
            # For each found node, get neighbors and statements
            for result in vector_results:
                node_id = result.get('id')
                if not node_id:
                    continue
                
                # Add the node itself
                nodes.append(result)
                
                # Get outgoing edges and their target nodes
                query_outgoing = """
                MATCH (n:ConceptualNode {id: $node_id})-[r:CONCEPTUAL_EDGE]->(target:ConceptualNode)
                WHERE r.tx_time_to IS NULL
                  AND target.tx_time_to IS NULL
                RETURN r, target
                """
                
                result_out = graph.query(query_outgoing, {"node_id": node_id})
                for row in result_out.result_set:
                    edge = row[0]
                    target_node = row[1]
                    if hasattr(edge, 'properties'):
                        edges.append(dict(edge.properties))
                    if hasattr(target_node, 'properties'):
                        nodes.append(dict(target_node.properties))
                
                # Get incoming edges and their source nodes
                query_incoming = """
                MATCH (source:ConceptualNode)-[r:CONCEPTUAL_EDGE]->(n:ConceptualNode {id: $node_id})
                WHERE r.tx_time_to IS NULL
                  AND source.tx_time_to IS NULL
                RETURN r, source
                """
                
                result_in = graph.query(query_incoming, {"node_id": node_id})
                for row in result_in.result_set:
                    edge = row[0]
                    source_node = row[1]
                    if hasattr(edge, 'properties'):
                        edges.append(dict(edge.properties))
                    if hasattr(source_node, 'properties'):
                        nodes.append(dict(source_node.properties))
                
                # Get statements about this node
                node_statements = self.memory_manager.get_statements_for_concept(
                    node_id,
                    graph_name=self.graph_name
                )
                statements.extend(node_statements)
            
            # Remove duplicates (by id)
            unique_nodes = {n.get('id'): n for n in nodes if n.get('id')}.values()
            unique_edges = {e.get('id'): e for e in edges if e.get('id')}.values()
            
            expanded_subgraph = {
                "nodes": list(unique_nodes),
                "edges": list(unique_edges),
                "statements": statements
            }
            
            logger.info(f"Graph expansion: {len(expanded_subgraph['nodes'])} nodes, "
                       f"{len(expanded_subgraph['edges'])} edges, "
                       f"{len(expanded_subgraph['statements'])} statements")
            
            return {
                **state,
                "expanded_subgraph": expanded_subgraph,
                "messages": state.get("messages", []) + [
                    SystemMessage(content=f"Expanded to {len(expanded_subgraph['nodes'])} nodes, "
                                        f"{len(expanded_subgraph['edges'])} edges, "
                                        f"{len(expanded_subgraph['statements'])} statements")
                ]
            }
            
        except Exception as e:
            logger.error(f"Graph expansion failed: {e}")
            return {
                **state,
                "error": f"Graph expansion failed: {str(e)}",
                "expanded_subgraph": {"nodes": [], "edges": [], "statements": []}
            }
    
    def response_synthesis_node(self, state: RetrievalState) -> RetrievalState:
        """
        Use LLM to synthesize response from subgraph context.
        
        Args:
            state: Current retrieval state
        
        Returns:
            Final state with synthesized response
        """
        try:
            query = state.get("query", "")
            expanded_subgraph = state.get("expanded_subgraph", {})
            
            nodes = expanded_subgraph.get("nodes", [])
            edges = expanded_subgraph.get("edges", [])
            statements = expanded_subgraph.get("statements", [])
            
            if not nodes:
                return {
                    **state,
                    "response": "I don't have any relevant information in my memory about that.",
                    "metadata": {
                        "sources_count": 0,
                        "confidence": 0.0
                    }
                }
            
            # Format subgraph as context string
            context_parts = []
            
            # Add nodes
            context_parts.append("=== Knowledge Graph Entities ===")
            for node in nodes:
                node_str = f"- {node.get('label', 'Entity')}: {node.get('name', 'Unknown')}"
                if node.get('properties'):
                    node_str += f" (properties: {node.get('properties')})"
                node_str += f" [graph_type: {node.get('graph_type', 'unknown')}]"
                context_parts.append(node_str)
            
            # Add edges
            if edges:
                context_parts.append("\n=== Relationships ===")
                for edge in edges:
                    edge_str = f"- {edge.get('edge_type', 'RELATED_TO')}"
                    context_parts.append(edge_str)
            
            # Add statements
            if statements:
                context_parts.append("\n=== Statements and Claims ===")
                for stmt in statements:
                    stmt_str = f"- Source: {stmt.get('source_name', 'Unknown')}"
                    if stmt.get('attributes'):
                        stmt_str += f", Claims: {stmt.get('attributes')}"
                    stmt_str += f", Confidence: {stmt.get('confidence', 1.0)}"
                    context_parts.append(stmt_str)
            
            context = "\n".join(context_parts)
            
            # Create synthesis prompt
            system_prompt = """You are an AI memory retrieval assistant. Based on the knowledge graph context provided, 
answer the user's query. If there are multiple sources with conflicting information, mention all perspectives and their sources.
If the information is not sufficient to answer the query, say so clearly."""
            
            human_prompt = f"""Context from knowledge graph:
{context}

User query: {query}

Please provide a comprehensive answer based on the available information. Include source attribution when relevant."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Call LLM
            response_message = self.llm.invoke(messages)
            response_text = response_message.content
            
            # Build metadata
            metadata = {
                "sources_count": len(nodes),
                "statements_count": len(statements),
                "edges_count": len(edges),
                "graph_types": list(set([n.get('graph_type', 'unknown') for n in nodes])),
                "confidence": sum([n.get('similarity_score', 0) for n in nodes]) / len(nodes) if nodes else 0.0
            }
            
            logger.info(f"Response synthesized successfully")
            
            return {
                **state,
                "response": response_text,
                "metadata": metadata,
                "messages": state.get("messages", []) + messages + [response_message]
            }
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {e}")
            return {
                **state,
                "error": f"Response synthesis failed: {str(e)}",
                "response": "I encountered an error while processing your query.",
                "metadata": {"sources_count": 0, "confidence": 0.0}
            }
    
    def search(
        self,
        query: str,
        graph_types: Optional[List[GraphType]] = None
    ) -> Dict[str, Any]:
        """
        Execute hybrid search and return response.
        
        Args:
            query: User query string
            graph_types: Optional list of graph types to search (defaults to both)
        
        Returns:
            Dict with query, response, and metadata
        """
        try:
            # Default to both graphs if not specified
            if graph_types is None:
                graph_types = [GraphType.INTERNAL, GraphType.EXTERNAL]
            
            initial_state: RetrievalState = {
                "query": query,
                "query_embedding": [],
                "graph_types": graph_types,
                "vector_results": [],
                "expanded_subgraph": {},
                "response": "",
                "metadata": {},
                "messages": [],
                "error": None
            }
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "status": "completed" if not final_state.get("error") else "failed",
                "error": final_state.get("error"),
                "query": query,
                "response": final_state.get("response", ""),
                "metadata": final_state.get("metadata", {}),
                "graph_types_searched": [gt.value for gt in graph_types]
            }
            
        except Exception as e:
            logger.error(f"Search workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "query": query,
                "response": "I encountered an error while searching my memory.",
                "metadata": {"sources_count": 0, "confidence": 0.0},
                "graph_types_searched": [gt.value for gt in graph_types] if graph_types else []
            }

