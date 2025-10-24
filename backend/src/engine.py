from .memory.manager import MemoryManager
from .memory.stm import ShortTermMemoryBuffer
from .memory.consolidation import ConsolidationGraph
from .memory.retrieval import RetrievalGraph
from .memory.schema import GraphType
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class CognitiveEngine:
    """
    A high-level facade for the agent's memory system.
    
    This class orchestrates the different components of the memory system,
    including short-term memory, long-term memory, consolidation, and retrieval.
    """
    
    def __init__(self):
        """Initializes the Cognitive Engine and its components."""
        host = os.getenv("FALKORDB_HOST", "localhost")
        port = int(os.getenv("FALKORDB_PORT", "6379"))
        
        logger.info(f"Initializing CognitiveEngine with FalkorDB at {host}:{port}")
        
        self.memory_manager = MemoryManager(host=host, port=port)
        self.stm_buffer = ShortTermMemoryBuffer(host=host, port=port)
        self.consolidation_graph = ConsolidationGraph(
            stm_buffer=self.stm_buffer,
            memory_manager=self.memory_manager
        )
        self.retrieval_graph = RetrievalGraph(
            memory_manager=self.memory_manager
        )
        logger.info("CognitiveEngine initialized successfully.")

    def add_observation(self, observation: str) -> int:
        """
        Adds a new observation to the short-term memory buffer.
        
        Args:
            observation: The text observation to add.
            
        Returns:
            The new size of the STM buffer.
        """
        logger.info(f"Adding observation to STM: '{observation}'")
        from .memory.stm import Observation
        obs = Observation(content=observation, timestamp=datetime.now())
        self.stm_buffer.add(obs)
        return self.stm_buffer.size()

    def get_stm_status(self) -> Dict[str, Any]:
        """
        Gets the current status of the STM buffer.
        
        Returns:
            A dictionary with STM status information.
        """
        size = self.stm_buffer.size()
        is_empty = self.stm_buffer.is_empty()
        return {
            "stm_size": size,
            "is_empty": is_empty,
            "ready_for_consolidation": size > 0
        }

    def consolidate_memory(self) -> Dict[str, Any]:
        """
        Runs the memory consolidation process (STM -> LTM).
        
        Returns:
            A dictionary with the results of the consolidation process.
        """
        logger.info("Starting memory consolidation process.")
        result = self.consolidation_graph.run()
        logger.info(f"Memory consolidation finished with status: {result['status']}")
        return result

    def search_memory(
        self, 
        query: str, 
        graph_types: Optional[List[GraphType]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Searches the long-term memory.
        
        Args:
            query: The search query.
            graph_types: Optional list of graph types to search in.
            top_k: The number of top results to retrieve.
            
        Returns:
            A dictionary with the search results.
        """
        logger.info(f"Searching memory for query: '{query}' with top_k={top_k}")
        self.retrieval_graph.top_k = top_k
        result = self.retrieval_graph.search(query=query, graph_types=graph_types)
        logger.info(f"Memory search finished with status: {result['status']}")
        return result

    def get_full_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieves the entire knowledge graph from LTM.
        
        Returns:
            A dictionary containing lists of all nodes and links.
        """
        logger.info("Retrieving full knowledge graph from LTM.")
        return self.memory_manager.get_full_graph()
