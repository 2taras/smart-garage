from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_status: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Client connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("Client disconnected")

    async def broadcast(self, message: str, exclude: WebSocket = None):
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")

    def update_status(self, status: dict):
        self.device_status = status

    def get_status(self) -> dict:
        return self.device_status

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await manager.connect(websocket)
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle status updates
                if "type" in message and message["type"] == "status":
                    manager.update_status(message)
                    # Broadcast status to all clients
                    await manager.broadcast(data, exclude=websocket)
                    logger.info(f"Status update: {message}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.post("/api/garage/command")
async def send_command(command: str):
    """
    Send command to garage device
    Commands: "open" or "close"
    """
    if not manager.active_connections:
        return {"error": "Garage not connected"}
    
    message = json.dumps({"command": command})
    await manager.broadcast(message)
    return {"status": "Command sent"}

@app.get("/api/garage/status")
async def get_status():
    """
    Get current status of the garage
    """
    status = manager.get_status()
    if not status:
        return {"error": "Garage not connected or status not available"}
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)