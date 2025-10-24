from .engine import CognitiveEngine
from fastapi import WebSocket
from typing import List
import logging

# Moved ConnectionManager here to break circular import
class ConnectionManager:
    """Управління WebSocket з'єднаннями"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"✅ WebSocket підключено. Всього з'єднань: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"❌ WebSocket відключено. Всього з'єднань: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Відправляє повідомлення всім підключеним клієнтам"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logging.warning(f"⚠️  Помилка відправки: {e}")

# Instantiate singletons
engine = CognitiveEngine()
manager = ConnectionManager()

def get_engine():
    """Dependency injector for the CognitiveEngine."""
    return engine

def get_manager():
    """Dependency injector for the ConnectionManager."""
    return manager
