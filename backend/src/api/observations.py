from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from ..engine import CognitiveEngine
from ..dependencies import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["observations"])

class ObservationRequest(BaseModel):
    """Request model for adding an observation."""
    observation: str

class ObservationResponse(BaseModel):
    """Response model for adding an observation."""
    status: str
    stm_size: int

@router.post("/observations", response_model=ObservationResponse)
async def add_observation(
    request: ObservationRequest,
    engine: CognitiveEngine = Depends(get_engine)
) -> ObservationResponse:
    """Adds an observation to the Short-Term Memory buffer."""
    if not request.observation or not request.observation.strip():
        raise HTTPException(status_code=400, detail="Observation cannot be empty.")
    try:
        new_size = engine.add_observation(request.observation)
        return ObservationResponse(status="success", stm_size=new_size)
    except Exception as e:
        logger.error(f"Failed to add observation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
