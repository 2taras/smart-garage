from sqlalchemy.orm import Session
from app.crud.crud_user import crud_user
from app.schemas.user import UserCreate
from app.core.config import settings
from app.models import models

def init_db(db: Session) -> None:
    # Create initial admin user if doesn't exist
    user = crud_user.get_by_telegram_id(db, telegram_id=settings.ADMIN_TELEGRAM_ID)
    if not user:
        user_in = UserCreate(
            telegram_id=settings.ADMIN_TELEGRAM_ID,
            role="admin"
        )
        crud_user.create(db, obj_in=user_in)