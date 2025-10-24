"""
AgentMind Backend - FastAPI з WebSocket підтримкою
Етапи 0-3: HTTP + WebSocket + Memory Consolidation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import asyncio
from typing import List

from .api.consolidation import router as consolidation_router
from .api.retrieval import router as retrieval_router
from .api.observations import router as observations_router
from .api.chat import router as chat_router
from .dependencies import get_engine, get_manager, ConnectionManager, engine as cognitive_engine

app = FastAPI(
    title="AgentMind Backend",
    description="Платформа для управління пам'яттю самонавчальних ШІ-агентів",
    version="0.1.0"
)

# CORS налаштування для фронтенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(consolidation_router)
app.include_router(retrieval_router)
app.include_router(observations_router)
app.include_router(chat_router)


# Add a new router for graph operations
graph_router = APIRouter(prefix="/api", tags=["graph"])

@graph_router.get("/graph/full")
async def get_full_graph(engine: "CognitiveEngine" = Depends(get_engine)):
    """Retrieves the entire knowledge graph."""
    try:
        return engine.get_full_graph()
    except Exception as e:
        # We need a logger here. Let's add it.
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get full graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(graph_router)


# Get singleton manager instance from dependencies
manager = get_manager()


# HTTP Endpoints
@app.get("/")
async def root():
    return {"message": "AgentMind Backend is running"}


# WebSocket Connection Manager
# class ConnectionManager:
#     """Управління WebSocket з'єднаннями"""
#
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#
#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#         print(f"✅ WebSocket підключено. Всього з'єднань: {len(self.active_connections)}")
#
#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)
#         print(f"❌ WebSocket відключено. Всього з'єднань: {len(self.active_connections)}")
#
#     async def send_personal_message(self, message: dict, websocket: WebSocket):
#         await websocket.send_json(message)
#
#     async def broadcast(self, message: dict):
#         """Відправляє повідомлення всім підключеним клієнтам"""
#         for connection in self.active_connections:
#             try:
#                 await connection.send_json(message)
#             except Exception as e:
#                 print(f"⚠️  Помилка відправки: {e}")


# Dependency injectors are now in dependencies.py
# def get_engine():
#     return engine
#
# def get_manager():
#     return manager


# WebSocket endpoint
@app.websocket("/ws/graph-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time graph updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Тестовий ендпоінт для broadcast
@app.post("/api/broadcast")
async def broadcast_message(message: str, manager: ConnectionManager = Depends(get_manager)):
    """Тестовий ендпоінт для відправки broadcast повідомлення"""
    await manager.broadcast({
        "type": "broadcast",
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "sent", "recipients": len(manager.active_connections)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

