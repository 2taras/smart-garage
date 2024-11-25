from fastapi import APIRouter
from app.api.v1.endpoints import auth, garages, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(garages.router, prefix="/garages", tags=["garages"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])