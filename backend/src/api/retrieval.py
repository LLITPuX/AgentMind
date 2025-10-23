"""
FastAPI endpoints for memory retrieval.

Provides API for hybrid search (vector + graph) in LTM.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
import os

from ..memory.retrieval import RetrievalGraph
from ..memory.manager import MemoryManager
from ..memory.schema import GraphType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["retrieval"])


# Dependency injection
def get_memory_manager() -> MemoryManager:
    """Get MemoryManager instance."""
    host = os.getenv("FALKORDB_HOST", "localhost")
    port = int(os.getenv("FALKORDB_PORT", "6379"))
    return MemoryManager(host=host, port=port)


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query string")
    graph_types: Optional[List[str]] = Field(
        default=None,
        description="Graph types to search: 'internal', 'external', or both (default: both)"
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top results to retrieve (1-20)"
    )


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    status: str
    query: str
    response: str
    metadata: Dict[str, Any]
    graph_types_searched: List[str]
    error: Optional[str] = None


@router.post("/search", response_model=SearchResponse)
async def search_memory(
    request: SearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> SearchResponse:
    """
    Search memory using hybrid retrieval (vector + graph).
    
    This endpoint performs the following:
    1. Vector search to find semantically similar nodes
    2. Graph expansion to include neighbors and statements
    3. LLM-based response synthesis with source attribution
    
    Args:
        request: Search request with query and optional filters
        memory_manager: Injected MemoryManager instance
    
    Returns:
        SearchResponse with synthesized answer and metadata
    
    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(f"Search request: '{request.query}'")
        
        # Parse graph_types from strings to GraphType enums
        graph_types = None
        if request.graph_types:
            try:
                graph_types = [
                    GraphType(gt.lower()) for gt in request.graph_types
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid graph_type. Must be 'internal' or 'external': {e}"
                )
        
        # Create retrieval graph
        retrieval_graph = RetrievalGraph(
            memory_manager=memory_manager,
            top_k=request.top_k
        )
        
        # Execute search
        result = retrieval_graph.search(
            query=request.query,
            graph_types=graph_types
        )
        
        if result["status"] == "failed":
            logger.error(f"Search failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Search failed: {result.get('error')}"
            )
        
        logger.info(f"Search completed: {result['metadata'].get('sources_count', 0)} sources")
        
        return SearchResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search error: {str(e)}"
        )


@router.get("/search/status")
async def get_search_status(
    memory_manager: MemoryManager = Depends(get_memory_manager)
) -> Dict[str, Any]:
    """
    Get search system status.
    
    Returns information about available memory graphs and statistics.
    
    Returns:
        Dict with status information
    """
    try:
        # Get graph statistics
        stats = memory_manager.get_graph_stats("agentmind_ltm")
        
        return {
            "status": "ready",
            "graph_stats": stats,
            "available_graph_types": ["internal", "external"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get search status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

