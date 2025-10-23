"""
FastAPI endpoints for memory consolidation.

Provides API for triggering STM to LTM consolidation process.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os

from ..memory.consolidation import ConsolidationGraph
from ..memory.stm import ShortTermMemoryBuffer
from ..memory.manager import MemoryManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["consolidation"])


# Dependency injection
def get_stm_buffer() -> ShortTermMemoryBuffer:
    """Get STM buffer instance."""
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    return ShortTermMemoryBuffer(host=host, port=port)


def get_memory_manager() -> MemoryManager:
    """Get MemoryManager instance."""
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    return MemoryManager(host=host, port=port)


class ConsolidationResponse(BaseModel):
    """Response model for consolidation endpoint."""
    status: str
    observations_processed: int
    entities_extracted: int
    relations_extracted: int
    nodes_created: int
    statements_created: int
    error: str = None


@router.post("/consolidate", response_model=ConsolidationResponse)
async def trigger_consolidation(
    stm_buffer: ShortTermMemoryBuffer = Depends(get_stm_buffer),
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> ConsolidationResponse:
    """
    Trigger STM to LTM consolidation process.
    
    Workflow:
    1. Fetches all observations from ShortTermMemory
    2. Uses LLM to extract entities and relationships
    3. Deduplicates against existing knowledge graph
    4. Saves new ConceptualNodes, ConceptualEdges, and Statements
    5. Clears processed observations from STM
    
    Returns:
        ConsolidationResponse with statistics about the consolidation
    
    Raises:
        HTTPException: If consolidation fails
    """
    try:
        logger.info("Starting consolidation process")
        
        # Create consolidation graph
        consolidation_graph = ConsolidationGraph(
            stm_buffer=stm_buffer,
            memory_manager=memory_manager
        )
        
        # Run consolidation
        result = consolidation_graph.run()
        
        if result["status"] == "failed":
            logger.error(f"Consolidation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Consolidation failed: {result.get('error')}"
            )
        
        logger.info(f"Consolidation completed: {result}")
        
        return ConsolidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Consolidation endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Consolidation error: {str(e)}"
        )


@router.get("/consolidation/status")
async def get_consolidation_status(
    stm_buffer: ShortTermMemoryBuffer = Depends(get_stm_buffer)
) -> Dict[str, Any]:
    """
    Get current status of STM buffer.
    
    Returns information about pending observations waiting for consolidation.
    
    Returns:
        Dict with STM buffer status
    """
    try:
        size = stm_buffer.size()
        is_empty = stm_buffer.is_empty()
        
        return {
            "stm_size": size,
            "is_empty": is_empty,
            "ready_for_consolidation": size > 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get consolidation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

