from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud.crud_user import crud_user
from app.schemas.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    user = crud_user.get_by_telegram_id(db, telegram_id=token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user

def check_admin_access(current_user: User = Depends(get_current_user)) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )

def verify_telegram_auth(auth_data: dict) -> bool:
    # TODO Implement Telegram authentication verification
    # https://core.telegram.org/widgets/login#checking-authorization
    return True