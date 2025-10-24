"""
FastAPI endpoints for memory consolidation.

Provides API for triggering STM to LTM consolidation process.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
import logging

from ..engine import CognitiveEngine
from ..dependencies import get_engine, get_manager, ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["consolidation"])


# Pydantic models remain the same
class ConsolidationResponse(BaseModel):
    """Response model for consolidation endpoint."""
    status: str
    observations_processed: int
    entities_extracted: int
    relations_extracted: int
    nodes_created: int
    statements_created: int
    error: str = ""


async def notify_graph_update(manager: ConnectionManager, engine: CognitiveEngine):
    """Task to send graph update notifications to all connected clients."""
    logger.info("Broadcasting graph update to all WebSocket clients.")
    try:
        full_graph = engine.get_full_graph()
        await manager.broadcast({
            "type": "graph_update",
            "payload": full_graph
        })
        logger.info(f"Successfully broadcasted graph update to {len(manager.active_connections)} clients.")
    except Exception as e:
        logger.error(f"Failed to broadcast graph update: {e}")


@router.post("/consolidate", response_model=ConsolidationResponse)
async def trigger_consolidation(
    background_tasks: BackgroundTasks,
    engine: CognitiveEngine = Depends(get_engine),
    manager: ConnectionManager = Depends(get_manager)
) -> ConsolidationResponse:
    """
    Trigger STM to LTM consolidation process using the CognitiveEngine.
    On success, it triggers a background task to notify clients via WebSocket.
    """
    try:
        logger.info("Endpoint trigger_consolidation called")
        result = engine.consolidate_memory()
        
        if result["status"] == "failed":
            logger.error(f"Consolidation failed: {result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Consolidation failed: {result.get('error')}"
            )
        
        # On success, schedule a notification
        background_tasks.add_task(notify_graph_update, manager, engine)

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
    engine: CognitiveEngine = Depends(get_engine)
) -> Dict[str, Any]:
    """
    Get current status of STM buffer via CognitiveEngine.
    """
    try:
        return engine.get_stm_status()
    except Exception as e:
        logger.error(f"Failed to get consolidation status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )

