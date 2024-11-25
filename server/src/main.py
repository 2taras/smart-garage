from fastapi import FastAPI, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import asyncio

from app.core.config import settings
from app.core.security import get_current_user
from app.api.v1.api import api_router
from app.websockets.manager import WebSocketManager
from app.telegram.bot import TelegramBot

app = FastAPI(title="Smart Garage API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager
ws_manager = WebSocketManager()

# Initialize Telegram bot
telegram_bot = TelegramBot(settings.TELEGRAM_BOT_TOKEN)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.websocket("/ws/garage/{garage_id}")
async def websocket_endpoint(websocket: WebSocket, garage_id: str):
    await ws_manager.connect(websocket, garage_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_message(garage_id, data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket, garage_id)

@app.on_event("startup")
async def startup_event():
    await telegram_bot.start()

@app.on_event("shutdown")
async def shutdown_event():
    await telegram_bot.stop()