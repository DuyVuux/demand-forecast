from __future__ import annotations

import os
import time
from datetime import timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Settings helpers
class _Settings:
    # Prefer new env names; fall back to legacy ANALYSIS_JWT_SECRET for compatibility
    JWT_SECRET: str = os.getenv("JWT_SECRET", os.getenv("ANALYSIS_JWT_SECRET", "devsecret_change_me"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRES_MIN: int = int(os.getenv("ACCESS_TOKEN_EXPIRES_MIN", "60"))
    REFRESH_TOKEN_EXPIRES_MIN: int = int(os.getenv("REFRESH_TOKEN_EXPIRES_MIN", str(7 * 24 * 60)))


settings = _Settings()


# JWT helpers
bearer_scheme = HTTPBearer(auto_error=False)


def create_token(subject: str, token_type: str, expires_in_seconds: int, extra: Optional[Dict[str, Any]] = None) -> str:
    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,  # 'access' | 'refresh'
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, role: str, extra: Optional[Dict[str, Any]] = None) -> str:
    return create_token(
        subject,
        token_type="access",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRES_MIN * 60,
        extra={"role": role, **(extra or {})},
    )


def create_refresh_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    return create_token(
        subject,
        token_type="refresh",
        expires_in_seconds=settings.REFRESH_TOKEN_EXPIRES_MIN * 60,
        extra=extra,
    )


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token hết hạn") from e
    except jwt.InvalidTokenError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ") from e


# Password hashing

def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Dependencies

def get_current_user_claims(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Dict[str, Any]:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Thiếu Bearer token")
    claims = decode_token(creds.credentials)
    if claims.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ (type)")
    return claims


def require_roles(allowed: set[str]):
    def _checker(claims: Dict[str, Any] = Depends(get_current_user_claims)) -> Dict[str, Any]:
        role = str(claims.get("role", "user"))
        if role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền")
        return claims

    return _checker


# Optional middleware to attach claims (not enabled by default)
class AuthContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        try:
            auth = request.headers.get("authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]
                request.state.claims = decode_token(token)  # type: ignore[attr-defined]
        except Exception:
            # Don't block the request; leave unauthenticated
            request.state.claims = None  # type: ignore[attr-defined]
        return await call_next(request)
