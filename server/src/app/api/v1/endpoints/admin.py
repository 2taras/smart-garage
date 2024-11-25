from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.security import get_current_user, check_admin_access
from app.schemas import user as user_schemas
from app.schemas import garage as garage_schemas
from app.schemas import log as log_schemas
from app.crud import crud_user, crud_garage, crud_access_log
from app.db.session import get_db

router = APIRouter(dependencies=[Depends(check_admin_access)])

@router.get("/users", response_model=List[user_schemas.User])
def get_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all users (admin only)
    """
    users = crud_user.get_multi(db, skip=skip, limit=limit)
    return users

@router.get("/logs", response_model=List[log_schemas.AccessLog])
def get_logs(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve system logs (admin only)
    """
    logs = crud_access_log.get_multi(db, skip=skip, limit=limit)
    return logs

@router.post("/garages/approve", response_model=garage_schemas.Garage)
def approve_garage(
    *,
    db: Session = Depends(get_db),
    approval: garage_schemas.GarageApproval,
) -> Any:
    """
    Approve new garage device (admin only)
    """
    garage = crud_garage.get_by_esp32_id(db, esp32_id=approval.esp32_identifier)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    
    garage_update = garage_schemas.GarageUpdate(
        name=approval.name,
        is_approved=True
    )
    garage = crud_garage.update(db, db_obj=garage, obj_in=garage_update)
    return garage

@router.put("/garages/{garage_id}", response_model=garage_schemas.Garage)
def update_garage_admin(
    *,
    db: Session = Depends(get_db),
    garage_id: int,
    garage_in: garage_schemas.GarageUpdate,
) -> Any:
    """
    Update garage settings (admin only)
    """
    garage = crud_garage.get(db, id=garage_id)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    garage = crud_garage.update(db, db_obj=garage, obj_in=garage_in)
    return garage