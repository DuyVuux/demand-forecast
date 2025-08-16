from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=128)
    email: Optional[EmailStr] = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
