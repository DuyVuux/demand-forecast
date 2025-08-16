from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..core import security
from ..schemas.user_schema import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from ..services.auth_service import (
    authenticate_user,
    create_user,
    generate_tokens,
    refresh_tokens,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, summary="Đăng ký tài khoản mới")
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserOut:
    user = create_user(
        db,
        username=payload.username,
        password=payload.password,
        email=payload.email,
        role="user",
    )
    return user  # pydantic will serialize via orm_mode


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập và nhận JWT")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    access_token, refresh_token, access_exp, refresh_exp = generate_tokens(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_exp,
        refresh_expires_in=refresh_exp,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Làm mới token bằng refresh token")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    access_token, refresh_token, access_exp, refresh_exp = refresh_tokens(db, payload.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_exp,
        refresh_expires_in=refresh_exp,
    )


@router.get("/me", response_model=UserOut, summary="Lấy thông tin tài khoản hiện tại")
def me(claims=Depends(security.get_current_user_claims), db: Session = Depends(get_db)) -> UserOut:
    # Resolve user by username in claims (sub)
    from ..services.auth_service import get_user_by_username

    user = get_user_by_username(db, claims.get("sub"))
    if not user:
        # Nếu user đã bị xóa nhưng token còn hiệu lực: trả về thông tin tối thiểu từ claims
        from ..models.user import User

        temp = User(
            id=0,
            username=str(claims.get("sub")),
            email=None,
            password_hash="",
            role=str(claims.get("role", "user")),
            is_active=True,
        )
        # type: ignore[return-value]
        return temp  # serialized via orm_mode-compatible fields
    return user

