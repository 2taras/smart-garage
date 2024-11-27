from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core import security
from app.core.security import get_current_user
from app.schemas import user as user_schemas
from app.crud.crud_user import crud_user
from app.db.session import get_db

router = APIRouter()

@router.post("/telegram", response_model=user_schemas.User)
def telegram_login(
    *,
    db: Session = Depends(get_db),
    auth_data: user_schemas.TelegramAuth
) -> Any:
    """
    Authenticate user with Telegram login widget data
    """
    if not security.verify_telegram_auth(auth_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data",
        )
    
    user = crud_user.get_by_telegram_id(db, telegram_id=auth_data.id)
    if not user:
        user = crud_user.create_with_telegram(db, obj_in=auth_data)
    return user

@router.get("/me", response_model=user_schemas.User)
def read_current_user(
    current_user: user_schemas.User = Depends(get_current_user)
) -> Any:
    """
    Get current user information
    """
    return current_user