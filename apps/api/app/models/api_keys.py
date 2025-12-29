"""API Key model for authentication."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ApiKey(Base):
    """
    API Key for authenticating external requests (Alex persona).
    
    Supports rate limiting and usage tracking.
    """

    __tablename__ = "api_keys"

    # Key identification
    key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Owner information
    owner_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, default=10000)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Expiration (optional)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def is_valid(self) -> bool:
        """Check if the API key is valid and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def record_usage(self) -> None:
        """Record a usage of this API key."""
        self.last_used_at = datetime.now(timezone.utc)
        self.total_requests += 1

