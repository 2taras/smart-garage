from fastapi import WebSocket
from typing import Dict, Set, Optional
import json
import asyncio
from datetime import datetime

from app.crud.crud_garage import crud_garage
from app.schemas.garage import GarageState
from app.core.config import settings
from app.telegram.bot import telegram_bot

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.web_clients: Set[WebSocket] = set()
        self.garage_states: Dict[str, GarageState] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        
        if client_id.startswith("web_"):
            self.web_clients.add(websocket)
        else:
            self.active_connections[client_id] = websocket
            # Notify admin about ESP32 connection
            await self._notify_admin(f"ESP32 device {client_id} connected")

    async def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id.startswith("web_"):
            self.web_clients.remove(websocket)
        else:
            self.active_connections.pop(client_id, None)
            # Notify admin about ESP32 disconnection
            await self._notify_admin(f"ESP32 device {client_id} disconnected")

    async def send_command(self, garage_id: str, action: str) -> bool:
        if garage_id not in self.active_connections:
            return False

        try:
            message = {
                "type": "command",
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.active_connections[garage_id].send_json(message)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    async def broadcast_state(self, garage_id: str, state: GarageState):
        message = {
            "type": "state_update",
            "garage_id": garage_id,
            "state": state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update stored state
        self.garage_states[garage_id] = state

        # Broadcast to all web clients
        for client in self.web_clients:
            try:
                await client.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to web client: {e}")

    async def handle_message(self, garage_id: str, message: dict):
        if message["type"] == "status":
            new_state = GarageState(message["state"])
            await self.broadcast_state(garage_id, new_state)
        
        # Handle other message types as needed

    async def _notify_admin(self, message: str):
        try:
            await telegram_bot.send_message(
                settings.ADMIN_TELEGRAM_ID,
                message
            )
        except Exception as e:
            print(f"Error notifying admin: {e}")

    def get_garage_state(self, garage_id: str) -> Optional[GarageState]:
        return self.garage_states.get(garage_id)