from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.security import create_access_token, verify_password
from app.services import record_audit


router = APIRouter(prefix="/auth", tags=["Authentication"])


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        given_name=user.given_name,
        family_name=user.family_name,
        is_active=user.is_active,
        roles=sorted(role.code for role in user.roles),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    role_codes = sorted(role.code for role in user.roles)
    token, expires_in = create_access_token(user.id, role_codes)
    record_audit(
        db,
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        action="LOGIN",
        after_data={"ip": request.client.host if request.client else None},
    )
    db.commit()
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    return serialize_user(user)
