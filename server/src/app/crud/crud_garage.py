from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.models import Garage
from app.schemas.garage import GarageCreate, GarageUpdate

class CRUDGarage:
    def get(self, db: Session, garage_id: int) -> Optional[Garage]:
        return db.query(Garage).filter(Garage.id == garage_id).first()

    def get_by_esp32_id(self, db: Session, esp32_id: str) -> Optional[Garage]:
        return db.query(Garage).filter(Garage.esp32_identifier == esp32_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Garage]:
        return db.query(Garage).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: GarageCreate) -> Garage:
        db_obj = Garage(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Garage, obj_in: GarageUpdate) -> Garage:
        update_data = obj_in.dict(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def user_has_access(self, db: Session, user_id: int, garage_id: int) -> bool:
        # Implement your access control logic here
        return True  # Temporary implementation

crud_garage = CRUDGarage()