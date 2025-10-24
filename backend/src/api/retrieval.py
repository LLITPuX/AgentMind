"""
FastAPI endpoints for memory retrieval.

Provides API for hybrid search (vector + graph) in LTM.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from ..engine import CognitiveEngine
from ..dependencies import get_engine
from ..memory.schema import GraphType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["retrieval"])


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
    engine: CognitiveEngine = Depends(get_engine)
) -> SearchResponse:
    """
    Search memory using the CognitiveEngine.
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
        
        # Execute search via engine
        result = engine.search_memory(
            query=request.query,
            graph_types=graph_types,
            top_k=request.top_k
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
    engine: CognitiveEngine = Depends(get_engine)
) -> Dict[str, Any]:
    """
    Get search system status via CognitiveEngine.
    """
    try:
        # Get graph statistics from memory manager via engine
        stats = engine.memory_manager.get_graph_stats("agentmind_ltm")
        
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

