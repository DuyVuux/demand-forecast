from __future__ import annotations

from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from ..models.user import User


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    *,
    username: str,
    password: str,
    email: Optional[str] = None,
    role: str = "user",
) -> User:
    if get_user_by_username(db, username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username đã tồn tại")
    if email and get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã tồn tại")

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai username hoặc password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản bị khóa")
    return user


def generate_tokens(user: User) -> Tuple[str, str, int, int]:
    access_token = create_access_token(subject=user.username, role=user.role)
    refresh_token = create_refresh_token(subject=user.username)
    # Expose expiry seconds for client (mirror settings in core.security)
    from ..core.security import settings as sec_settings

    return (
        access_token,
        refresh_token,
        sec_settings.ACCESS_TOKEN_EXPIRES_MIN * 60,
        sec_settings.REFRESH_TOKEN_EXPIRES_MIN * 60,
    )


def refresh_tokens(db: Session, refresh_token: str) -> Tuple[str, str, int, int]:
    # Validate refresh token and issue new pair
    from ..core.security import decode_token, settings as sec_settings

    claims = decode_token(refresh_token)
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh không hợp lệ")
    username = str(claims.get("sub"))
    user = get_user_by_username(db, username)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại hoặc bị khóa")
    access_token = create_access_token(subject=user.username, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.username)
    return (
        access_token,
        new_refresh_token,
        sec_settings.ACCESS_TOKEN_EXPIRES_MIN * 60,
        sec_settings.REFRESH_TOKEN_EXPIRES_MIN * 60,
    )
