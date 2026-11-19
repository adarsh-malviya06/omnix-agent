"""
SystemSetting model — persistent key-value configuration for business thresholds and governance policies.
"""

from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from omnix.db.base import Base, TimestampMixin


class SystemSetting(TimestampMixin, Base):
    """
    Persistent system and governance settings stored in the database.
    Survives application restarts and overrides environment variable defaults.
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="governance")
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<SystemSetting key={self.key} value={self.value}>"
