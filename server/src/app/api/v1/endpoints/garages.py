from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.security import get_current_user
from app.schemas import garage as garage_schemas
from app.crud import crud_garage, crud_access_log
from app.db.session import get_db
from app.websockets.manager import WebSocketManager
from app.schemas import user as user_schemas

router = APIRouter()

@router.get("/", response_model=List[garage_schemas.Garage])
def get_garages(
    db: Session = Depends(get_db),
    current_user: user_schemas.User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve all garages accessible by current user
    """
    garages = crud_garage.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return garages

@router.put("/{garage_id}", response_model=garage_schemas.Garage)
def update_garage(
    *,
    db: Session = Depends(get_db),
    garage_id: int,
    garage_in: garage_schemas.GarageUpdate,
    current_user: user_schemas.User = Depends(get_current_user),
) -> Any:
    """
    Update garage information
    """
    garage = crud_garage.get(db, id=garage_id)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    garage = crud_garage.update(db, db_obj=garage, obj_in=garage_in)
    return garage

@router.post("/{garage_id}/control")
async def control_garage(
    *,
    db: Session = Depends(get_db),
    garage_id: int,
    command: garage_schemas.GarageCommand,
    current_user: user_schemas.User = Depends(get_current_user),
) -> Any:
    """
    Control garage door (open/close)
    """
    garage = crud_garage.get(db, id=garage_id)
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    
    # Check if user has access to this garage
    if not crud_garage.user_has_access(db, user_id=current_user.id, garage_id=garage_id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Send command to ESP32 through WebSocket
    success = await WebSocketManager.send_command(garage.esp32_identifier, command.action)
    
    # Log the action
    crud_access_log.create(
        db,
        user_id=current_user.id,
        garage_id=garage_id,
        action=command.action,
        status="success" if success else "failure"
    )
    
    return {"status": "success" if success else "failure"}