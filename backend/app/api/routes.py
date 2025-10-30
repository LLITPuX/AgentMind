"""API routers and route registration."""

from __future__ import annotations

from fastapi import APIRouter, Depends
import redis.asyncio as redis

from ..dependencies.database import get_db_session
from ..dependencies.graph import get_falkordb, graph_query
from ..core.config import settings
from ..services.agent import run_analysis, run_conversation
from ..schemas.agent import (
    AnalysisRequest,
    AnalysisResponse,
    ConversationRequest,
    ConversationResponse,
)


router = APIRouter()


@router.get("/health/live", tags=["health"], summary="Liveness probe")
async def liveness_probe() -> dict[str, str]:
    """Endpoint used by orchestrators to ensure the service is responsive."""

    return {"status": "alive"}


@router.get("/health/db", tags=["health"], summary="Database connectivity check")
async def database_health(db=Depends(get_db_session)) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Ensure the database connection pool can acquire and release sessions."""

    await db.execute("SELECT 1")
    return {"status": "ok"}


@router.get("/graph/health", tags=["graph"], summary="FalkorDB connectivity check")
async def graph_health(client: redis.Redis = Depends(get_falkordb)) -> dict[str, object]:
    """Check FalkorDB availability and list graphs."""

    pong = await client.ping()
    graphs = await client.execute_command("GRAPH.LIST")
    return {"ping": pong, "graphs": graphs}


@router.post("/graph/query", tags=["graph"], summary="Run Cypher query on FalkorDB")
async def run_graph_query(
    q: str, client: redis.Redis = Depends(get_falkordb)
) -> dict[str, object]:
    """Execute a Cypher query against the configured graph."""

    result = await graph_query(client, settings.falkordb_graph, q)
    return {"result": result}


# -------------------------- Agent endpoints --------------------------


@router.post("/analysis", tags=["agent"], response_model=AnalysisResponse)
async def analysis_endpoint(payload: AnalysisRequest) -> AnalysisResponse:
    prefix = "User" if payload.message.sender == "user" else "AI"
    content = f"{prefix}: {payload.message.text}"

    try:
        import json

        schema = json.loads(payload.settings.jsonSchema)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid jsonSchema in settings") from exc

    analysis = await run_analysis(content, payload.settings.systemPrompt, schema)
    return AnalysisResponse(messageId=payload.message.id, analysis=analysis)


@router.post("/chat", tags=["agent"], response_model=ConversationResponse)
async def chat_endpoint(payload: ConversationRequest) -> ConversationResponse:
    # Map to Gemini contents format
    contents = [
        {
            "role": ("user" if m.sender == "user" else "model"),
            "parts": [{"text": m.text}],
        }
        for m in payload.messages
    ]
    text = await run_conversation(contents)
    return ConversationResponse(message=text or "")

