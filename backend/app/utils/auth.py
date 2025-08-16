from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Set

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Simple RBAC roles hierarchy
ROLE_ORDER = {"viewer": 1, "analyst": 2, "admin": 3}


def _get_secret() -> str:
    # Use env for production; default for local dev/demo
    # Prefer JWT_SECRET for compatibility with /auth module; fallback to ANALYSIS_JWT_SECRET
    return os.getenv("JWT_SECRET", os.getenv("ANALYSIS_JWT_SECRET", "devsecret_change_me"))


def create_access_token(
    subject: str,
    role: str = "viewer",
    expires_in_seconds: int = 3600,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, _get_secret(), algorithm="HS256")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret(), algorithms=["HS256"])  # type: ignore[no-any-return]
    except jwt.ExpiredSignatureError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token hết hạn") from e
    except jwt.InvalidTokenError as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ") from e


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Dict[str, Any]:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Thiếu Bearer token")
    payload = decode_token(creds.credentials)
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token thiếu thông tin")
    return {"username": payload["sub"], "role": payload["role"], "claims": payload}


def require_roles(allowed: Set[str]):
    def _checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = user.get("role", "viewer")
        if role not in ROLE_ORDER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vai trò không hợp lệ")
        if role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không đủ quyền")
        return user

    return _checker
