from sqlalchemy.orm import Session
from typing import List
from app.models.models import AccessLog
from app.schemas.log import AccessLogCreate

class CRUDAccessLog:
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[AccessLog]:
        return db.query(AccessLog).offset(skip).limit(limit).all()

    def create(
        self, db: Session, *, user_id: int, garage_id: int, action: str, status: str
    ) -> AccessLog:
        db_obj = AccessLog(
            user_id=user_id,
            garage_id=garage_id,
            action=action,
            status=status
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_access_log = CRUDAccessLog()