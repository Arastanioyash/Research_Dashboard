from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, verify_password
from app.db.user_store import user_store
from app.models.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    user = user_store.get_user(payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.username)
    return TokenResponse(access_token=token)
