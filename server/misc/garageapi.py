import os
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get base URL from environment variable with fallback
BASE_API_URL = os.getenv('GARAGE_API_URL')

class GarageAPI:
    @staticmethod
    async def open(thing: str, db: Session, user_id: int) -> str:
        # Map the commands to API endpoints
        command_map = {
            'left': 'open',
            'right': 'close'
        }
        
        if thing not in command_map:
            return "Invalid command"
            
        command = command_map[thing]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{BASE_API_URL}/api/garage/command',
                    params={'command': command},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()

            # Log the action
            
            return "Success"
            
        except Exception as e:
            # Still log failed attempts
            
            logger.error(f"API error: {str(e)}")
            return f"Error: {str(e)}"

    @staticmethod
    async def get_status() -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{BASE_API_URL}/api/garage/status',
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    response.raise_for_status()
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Failed to get status: {str(e)}")
            return {"error": str(e)}