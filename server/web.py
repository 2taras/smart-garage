from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import math
import random
import json
from pydantic import BaseModel
from misc.garageapi import GarageAPI
from misc.db import get_db, User, SystemConfig, Log

app = FastAPI()
security = HTTPBearer()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
GARAGE_LOCATION = json.loads(os.getenv("GARAGE_LOCATION"))
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"

class LocationData(BaseModel):
    latitude: float
    longitude: float

class LoginData(BaseModel):
    password: str

def distance(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "K") -> float:
    if lat1 == lat2 and lon1 == lon2:
        return 0
    
    theta = lon1 - lon2
    dist = (math.sin(math.radians(lat1)) * math.sin(math.radians(lat2)) + 
           math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
           math.cos(math.radians(theta)))
    dist = math.acos(dist)
    dist = math.degrees(dist)
    miles = dist * 60 * 1.1515
    
    return miles * 1.609344 if unit == "K" else miles * 0.8684 if unit == "N" else miles

class ConfigManager:
    @staticmethod
    def get_value(db, key: str):
        config = db.query(SystemConfig).filter_by(key=key).first()
        return config.value if config else None

    @staticmethod
    def set_value(db, key: str, value: str):
        config = db.query(SystemConfig).filter_by(key=key).first()
        if config:
            config.value = value
        else:
            config = SystemConfig(key=key, value=value)
            db.add(config)
        db.commit()

    @staticmethod
    def get_temp_password(db):
        password = ConfigManager.get_value(db, 'temp_password')
        if not password:
            password = str(random.randint(1000, 9999))
            ConfigManager.set_value(db, 'temp_password', password)
        return password

    @staticmethod
    def reset_temp_password(db):
        new_password = str(random.randint(1000, 9999))
        ConfigManager.set_value(db, 'temp_password', new_password)
        return new_password

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/login")
async def login(login_data: LoginData):
    db = next(get_db())
    current_pass = ConfigManager.get_temp_password(db)
    
    if login_data.password == current_pass:
        user_id = random.randint(10000, 99999)
        token = jwt.encode(
            {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(hours=24)
            },
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        ConfigManager.reset_temp_password(db)
        return {"token": token}
    
    raise HTTPException(status_code=401, detail="Invalid password")

@app.get("/api/status")
async def get_status(_: dict = Depends(get_current_user)):
    try:
        status = await GarageAPI.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    return {"valid": True}

@app.post("/api/garage/{action}")
async def control_garage(
    action: str,
    location: LocationData,
    user: dict = Depends(get_current_user)
):
    if action not in ['left', 'right']:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    dist = distance(
        location.latitude,
        location.longitude,
        GARAGE_LOCATION[0],
        GARAGE_LOCATION[1]
    )
    
    if dist > 1000:
        raise HTTPException(status_code=400, detail="Too far from garage")
    
    db = next(get_db())
    result = await GarageAPI.open(action, db, user["user_id"])
    
    log = Log(
        user=str(user["user_id"]),
        action=action,
        timestamp=int(datetime.utcnow().timestamp())
    )
    db.add(log)
    db.commit()
    
    return {"result": result}

@app.get("/api/logs")
async def get_logs(_: dict = Depends(get_current_user)):
    db = next(get_db())
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(50).all()
    return [{
        'timestamp': datetime.fromtimestamp(log.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        'user': log.user,
        'action': log.action
    } for log in logs]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)