from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.models import User
from app.schemas.user import UserCreate, TelegramAuth

class CRUDUser:
    def get(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_telegram_id(self, db: Session, telegram_id: str) -> Optional[User]:
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create_with_telegram(self, db: Session, obj_in: TelegramAuth) -> User:
        db_obj = User(
            telegram_id=str(obj_in.id),
            username=obj_in.username,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_user = CRUDUser()