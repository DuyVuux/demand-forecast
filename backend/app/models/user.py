from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(150), unique=True, nullable=False, index=True)
    email: Optional[str] = Column(String(255), unique=True, nullable=True, index=True)
    password_hash: str = Column(String(255), nullable=False)
    role: str = Column(String(32), nullable=False, default="user")  # roles: user, admin
    is_active: bool = Column(Boolean, nullable=False, default=True)

    created_at: datetime = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.id} username={self.username} role={self.role}>"
