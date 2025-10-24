"""
Consolidation Graph - LangGraph agent for STM to LTM consolidation.

Converts unstructured observations from ShortTermMemory into structured
ConceptualNodes, ConceptualEdges, and Statements in LongTermMemory.
"""

from typing import TypedDict, List, Annotated, Optional, Dict, Any
import operator
import logging
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from .stm import Observation, ShortTermMemoryBuffer
from .manager import MemoryManager
from .schema import ConceptualNode, ConceptualEdge, Statement, Source, GraphType, SourceType
from .extraction_models import ExtractedEntity, ExtractedRelation, ExtractionResult
from .embeddings import get_embedding_manager

logger = logging.getLogger(__name__)


class ConsolidationState(TypedDict):
    """
    State for the consolidation graph workflow.
    
    Tracks the progress of converting observations to structured knowledge.
    """
    observations: List[Observation]  # Input from STM
    extracted_entities: List[ExtractedEntity]  # Entities extracted by LLM
    extracted_relations: List[ExtractedRelation]  # Relations extracted by LLM
    deduplicated_nodes: List[str]  # IDs of created/found nodes
    created_statements: List[str]  # IDs of created statements
    entity_id_map: Dict[str, Optional[str]]  # Map of entity names to node IDs
    messages: Annotated[List[BaseMessage], operator.add]  # LLM conversation history
    error: Optional[str]  # Error message if any step fails


class ConsolidationGraph:
    """
    LangGraph agent for consolidating STM observations into LTM.
    
    Workflow:
    1. fetch_observations - Get observations from STM
    2. extract_entities - Use LLM to extract entities and relations
    3. deduplicate_entities - Find or create unique entities
    4. save_to_ltm - Save to FalkorDB
    5. cleanup_stm - Clear processed observations
    """
    
    def __init__(
        self,
        stm_buffer: ShortTermMemoryBuffer,
        memory_manager: MemoryManager,
        llm_model: str = "gpt-4o-mini",
        similarity_threshold: float = 0.85
    ):
        """
        Initialize ConsolidationGraph.
        
        Args:
            stm_buffer: ShortTermMemoryBuffer instance
            memory_manager: MemoryManager instance
            llm_model: OpenAI model to use for extraction
            similarity_threshold: Threshold for vector similarity deduplication
        """
        self.stm_buffer = stm_buffer
        self.memory_manager = memory_manager
        self.similarity_threshold = similarity_threshold
        
        # Initialize LLM with structured output
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0  # Deterministic for extraction
        )
        
        # Initialize embedding manager
        self.embedding_manager = get_embedding_manager()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"ConsolidationGraph initialized with model: {llm_model}")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine.
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(ConsolidationState)
        
        # Add nodes
        workflow.add_node("fetch_observations", self.fetch_observations_node)
        workflow.add_node("extract_entities", self.extract_entities_node)
        workflow.add_node("deduplicate_entities", self.deduplicate_entities_node)
        workflow.add_node("save_to_ltm", self.save_to_ltm_node)
        workflow.add_node("cleanup_stm", self.cleanup_stm_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("fetch_observations")
        workflow.add_edge("fetch_observations", "extract_entities")
        workflow.add_edge("extract_entities", "deduplicate_entities")
        workflow.add_edge("deduplicate_entities", "save_to_ltm")
        workflow.add_edge("save_to_ltm", "cleanup_stm")
        workflow.add_edge("cleanup_stm", END)
        
        return workflow.compile()
    
    def fetch_observations_node(self, state: ConsolidationState) -> ConsolidationState:
        """
        Fetch observations from STM buffer.
        
        Args:
            state: Current consolidation state
        
        Returns:
            Updated state with observations
        """
        try:
            observations = self.stm_buffer.get_all()
            logger.info(f"Fetched {len(observations)} observations from STM")
            
            return {
                **state,
                "observations": observations,
                "messages": state.get("messages", []) + [
                    SystemMessage(content=f"Fetched {len(observations)} observations for consolidation")
                ]
            }
        except Exception as e:
            logger.error(f"Failed to fetch observations: {e}")
            return {
                **state,
                "error": f"Failed to fetch observations: {str(e)}"
            }
    
    def extract_entities_node(self, state: ConsolidationState) -> ConsolidationState:
        """
        Extract entities and relations from observations using LLM.
        
        Args:
            state: Current consolidation state
        
        Returns:
            Updated state with extracted entities and relations
        """
        try:
            observations = state.get("observations", [])
            
            if not observations:
                logger.warning("No observations to extract from")
                return {
                    **state,
                    "extracted_entities": [],
                    "extracted_relations": []
                }
            
            # Combine observations into text
            observations_text = "\n".join([
                f"- {obs.content} (timestamp: {obs.timestamp})"
                for obs in observations
            ])
            
            # Create extraction prompt
            system_prompt = """You are an expert knowledge graph builder. Analyze observations and extract:
1. Entities (people, organizations, concepts, actions, preferences)
2. Relationships between entities
3. Temporal information when mentioned
4. Graph type:
   - "internal" for agent self-concept, user preferences, user information
   - "external" for external world knowledge, facts about companies, people, etc.

Return a JSON object with this exact structure:
{
  "entities": [
    {
      "label": "Person|Organization|Concept|Language|etc",
      "name": "Entity name",
      "graph_type": "internal|external",
      "properties": {}
    }
  ],
  "relations": [
    {
      "edge_type": "LIKES|WORKS_AT|KNOWS|etc",
      "from_entity_name": "Source entity name",
      "to_entity_name": "Target entity name",
      "graph_type": "internal|external",
      "properties": {}
    }
  ]
}"""
            
            human_prompt = f"""Observations:
{observations_text}

Extract entities and relationships."""
            
            # Use structured output with Pydantic
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Call LLM with JSON mode and parse manually
            # Use bind to set response_format
            llm_with_json = self.llm.bind(response_format={"type": "json_object"})
            response = llm_with_json.invoke(messages)
            
            # Parse JSON response
            import json
            response_json = json.loads(response.content)
            
            # Convert to ExtractionResult
            result = ExtractionResult(**response_json)
            
            logger.info(f"Extracted {len(result.entities)} entities and {len(result.relations)} relations")
            
            return {
                **state,
                "extracted_entities": result.entities,
                "extracted_relations": result.relations,
                "messages": state.get("messages", []) + messages + [
                    SystemMessage(content=f"Extracted {len(result.entities)} entities, {len(result.relations)} relations")
                ]
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to extract entities: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                **state,
                "error": f"Failed to extract entities: {str(e)}",
                "extracted_entities": [],
                "extracted_relations": []
            }
    
    def deduplicate_entities_node(self, state: ConsolidationState) -> ConsolidationState:
        """
        Deduplicate entities using exact match + vector similarity.
        
        For each extracted entity:
        1. Try exact match (name + label + graph_type)
        2. If not found, try vector similarity
        3. If still not found, mark for creation
        
        Args:
            state: Current consolidation state
        
        Returns:
            Updated state with entity ID mappings
        """
        try:
            extracted_entities = state.get("extracted_entities", [])
            entity_id_map: Dict[str, str] = {}  # entity_name -> node_id
            
            graph = self.memory_manager.get_graph("agentmind_ltm")
            
            for entity in extracted_entities:
                # Try exact match first
                exact_match_query = """
                MATCH (n:ConceptualNode {label: $label, name: $name, graph_type: $graph_type})
                WHERE n.tx_time_to IS NULL
                RETURN n.id AS id
                """
                
                result = graph.query(exact_match_query, {
                    "label": entity.label,
                    "name": entity.name,
                    "graph_type": entity.graph_type.value
                })
                
                if result.result_set:
                    # Exact match found
                    node_id = result.result_set[0][0]
                    entity_id_map[entity.name] = node_id
                    logger.debug(f"Exact match found for '{entity.name}': {node_id}")
                    continue
                
                # Try vector similarity
                # Get all nodes of same label and graph_type
                similar_nodes_query = """
                MATCH (n:ConceptualNode {label: $label, graph_type: $graph_type})
                WHERE n.tx_time_to IS NULL
                RETURN n.id AS id, n.name AS name
                """
                
                similar_result = graph.query(similar_nodes_query, {
                    "label": entity.label,
                    "graph_type": entity.graph_type.value
                })
                
                if similar_result.result_set:
                    # Generate embeddings and compare
                    query_embedding = self.embedding_manager.generate_embedding(entity.name)
                    
                    candidate_names = [row[1] for row in similar_result.result_set]
                    candidate_embeddings = self.embedding_manager.generate_embeddings(candidate_names)
                    
                    match_idx, similarity = self.embedding_manager.find_most_similar(
                        query_embedding,
                        candidate_embeddings,
                        self.similarity_threshold
                    )
                    
                    if match_idx >= 0:
                        # Similar node found
                        node_id = similar_result.result_set[match_idx][0]
                        entity_id_map[entity.name] = node_id
                        logger.debug(f"Similar match found for '{entity.name}': {node_id} (similarity: {similarity:.3f})")
                        continue
                
                # No match found - will create new node
                entity_id_map[entity.name] = None  # Placeholder
                logger.debug(f"No match found for '{entity.name}' - will create new")
            
            return {
                **state,
                "entity_id_map": entity_id_map
            }
            
        except Exception as e:
            logger.error(f"Failed to deduplicate entities: {e}")
            return {
                **state,
                "error": f"Failed to deduplicate entities: {str(e)}"
            }
    
    def save_to_ltm_node(self, state: ConsolidationState) -> ConsolidationState:
        """
        Save entities, relations, and statements to LTM.
        
        Args:
            state: Current consolidation state
        
        Returns:
            Updated state with created node and statement IDs
        """
        try:
            extracted_entities = state.get("extracted_entities", [])
            extracted_relations = state.get("extracted_relations", [])
            entity_id_map = state.get("entity_id_map", {})
            
            created_node_ids = []
            created_statement_ids = []
            
            # Create nodes for entities without matches
            for entity in extracted_entities:
                if entity.name in entity_id_map and entity_id_map[entity.name] is None:
                    # Create new node
                    node = ConceptualNode(
                        label=entity.label,
                        name=entity.name,
                        graph_type=entity.graph_type,
                        properties=entity.properties,
                        valid_from=entity.valid_from or datetime.now(),
                        valid_until=entity.valid_until or datetime(9999, 12, 31, 23, 59, 59)
                    )
                    
                    node_id = self.memory_manager.create_conceptual_node(node)
                    entity_id_map[entity.name] = node_id
                    created_node_ids.append(node_id)
                    logger.debug(f"Created new node for '{entity.name}': {node_id}")
                    
                    # Generate and store embedding for the node
                    try:
                        # Create text representation for embedding
                        properties_str = ", ".join([f"{k}: {v}" for k, v in entity.properties.items()])
                        text_for_embedding = f"{entity.label}: {entity.name}. {properties_str}" if properties_str else f"{entity.label}: {entity.name}"
                        
                        # Generate embedding
                        embedding = self.embedding_manager.generate_embedding(text_for_embedding)
                        
                        # Store embedding in node
                        self.memory_manager.store_node_embedding(node_id, embedding)
                        logger.debug(f"Stored embedding for node '{entity.name}'")
                    except Exception as e:
                        logger.warning(f"Failed to store embedding for node '{entity.name}': {e}")
            
            # Create relations
            for relation in extracted_relations:
                from_id = entity_id_map.get(relation.from_entity_name)
                to_id = entity_id_map.get(relation.to_entity_name)
                
                if not from_id or not to_id:
                    logger.warning(f"Skipping relation {relation.edge_type}: missing entity IDs")
                    continue
                
                # Check if edge already exists
                edge_exists_query = """
                MATCH (from:ConceptualNode {id: $from_id})-[r:CONCEPTUAL_EDGE {edge_type: $edge_type}]->(to:ConceptualNode {id: $to_id})
                WHERE r.tx_time_to IS NULL
                RETURN r.id AS id
                """
                
                graph = self.memory_manager.get_graph("agentmind_ltm")
                result = graph.query(edge_exists_query, {
                    "from_id": from_id,
                    "to_id": to_id,
                    "edge_type": relation.edge_type
                })
                
                if not result.result_set:
                    # Create new edge
                    edge = ConceptualEdge(
                        edge_type=relation.edge_type,
                        from_node_id=from_id,
                        to_node_id=to_id,
                        graph_type=relation.graph_type,
                        properties=relation.properties,
                        valid_from=relation.valid_from or datetime.now(),
                        valid_until=relation.valid_until or datetime(9999, 12, 31, 23, 59, 59)
                    )
                    
                    edge_id = self.memory_manager.create_conceptual_edge(edge)
                    logger.debug(f"Created edge: {relation.edge_type} ({from_id} -> {to_id})")
            
            # Create statements for each entity
            source = Source(
                name="ConsolidationAgent",
                type=SourceType.AGENT_INFERENCE,
                reliability_score=0.8
            )
            
            for entity in extracted_entities:
                node_id = entity_id_map.get(entity.name)
                if node_id:
                    stmt = Statement(
                        asserts_about_conceptual_id=node_id,
                        source=source,
                        attributes={
                            "extracted_from": "STM consolidation",
                            "properties": entity.properties
                        },
                        confidence=0.9
                    )
                    
                    stmt_id = self.memory_manager.create_statement(stmt)
                    created_statement_ids.append(stmt_id)
            
            logger.info(f"Saved {len(created_node_ids)} nodes and {len(created_statement_ids)} statements to LTM")
            
            return {
                **state,
                "deduplicated_nodes": list(entity_id_map.values()),
                "created_statements": created_statement_ids
            }
            
        except Exception as e:
            logger.error(f"Failed to save to LTM: {e}")
            return {
                **state,
                "error": f"Failed to save to LTM: {str(e)}"
            }
    
    def cleanup_stm_node(self, state: ConsolidationState) -> ConsolidationState:
        """
        Clear processed observations from STM.
        
        Args:
            state: Current consolidation state
        
        Returns:
            Final state
        """
        try:
            self.stm_buffer.clear()
            logger.info("Cleared processed observations from STM")
            
            return {
                **state,
                "messages": state.get("messages", []) + [
                    SystemMessage(content="Consolidation complete - STM cleared")
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup STM: {e}")
            return {
                **state,
                "error": f"Failed to cleanup STM: {str(e)}"
            }
    
    def run(self) -> Dict[str, Any]:
        """
        Run the consolidation workflow.
        
        Returns:
            Dict with consolidation results
        """
        try:
            initial_state: ConsolidationState = {
                "observations": [],
                "extracted_entities": [],
                "extracted_relations": [],
                "deduplicated_nodes": [],
                "created_statements": [],
                "entity_id_map": {},
                "messages": [],
                "error": None
            }
            
            final_state = self.graph.invoke(initial_state)
            
            return {
                "status": "completed" if not final_state.get("error") else "failed",
                "error": final_state.get("error") or "",
                "observations_processed": len(final_state.get("observations", [])),
                "entities_extracted": len(final_state.get("extracted_entities", [])),
                "relations_extracted": len(final_state.get("extracted_relations", [])),
                "nodes_created": len([n for n in final_state.get("deduplicated_nodes", []) if n]),
                "statements_created": len(final_state.get("created_statements", [])),
            }
            
        except Exception as e:
            logger.error(f"Consolidation workflow failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "observations_processed": 0,
                "entities_extracted": 0,
                "relations_extracted": 0,
                "nodes_created": 0,
                "statements_created": 0
            }

