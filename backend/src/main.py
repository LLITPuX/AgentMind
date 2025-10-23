"""
AgentMind Backend - FastAPI з WebSocket підтримкою
Етапи 0-3: HTTP + WebSocket + Memory Consolidation
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import asyncio
from typing import List

from .api.consolidation import router as consolidation_router

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


# WebSocket Connection Manager
class ConnectionManager:
    """Управління WebSocket з'єднаннями"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket підключено. Всього з'єднань: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket відключено. Всього з'єднань: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Відправляє повідомлення всім підключеним клієнтам"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️  Помилка відправки: {e}")


manager = ConnectionManager()


# HTTP Endpoints
@app.get("/")
async def root():
    """Головна сторінка API"""
    return {
        "service": "AgentMind Backend",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "websocket": "/ws/graph-updates"
        }
    }


@app.get("/health")
async def health_check():
    """Перевірка здоров'я сервісу"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_websockets": len(manager.active_connections)
    }


# WebSocket Endpoint
@app.websocket("/ws/graph-updates")
async def websocket_graph_updates(websocket: WebSocket):
    """
    WebSocket для оновлень графу в реальному часі
    
    Повідомлення, що надсилаються клієнту:
    - type: "connection" - підтвердження підключення
    - type: "graph_update" - оновлення графу
    - type: "ping" - keepalive повідомлення
    """
    await manager.connect(websocket)
    
    # Надсилаємо привітання
    await manager.send_personal_message({
        "type": "connection",
        "status": "connected",
        "message": "З'єднано з AgentMind Backend",
        "timestamp": datetime.now().isoformat()
    }, websocket)
    
    try:
        # Запускаємо keepalive в фоні
        async def keepalive():
            while True:
                try:
                    await asyncio.sleep(30)
                    await manager.send_personal_message({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }, websocket)
                except Exception:
                    break
        
        keepalive_task = asyncio.create_task(keepalive())
        
        # Слухаємо повідомлення від клієнта
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                print(f"📨 Отримано від клієнта: {message}")
                
                # Ехо відповідь
                await manager.send_personal_message({
                    "type": "echo",
                    "original": message,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Невалідний JSON",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
    
    except WebSocketDisconnect:
        keepalive_task.cancel()
        manager.disconnect(websocket)
        print("🔌 Клієнт відключився")
    
    except Exception as e:
        keepalive_task.cancel()
        manager.disconnect(websocket)
        print(f"❌ Помилка WebSocket: {e}")


# Тестовий ендпоінт для broadcast
@app.post("/api/broadcast")
async def broadcast_message(message: str):
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

