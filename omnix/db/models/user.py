"""
User model — platform user with role-based access within an organization.
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from omnix.db.base import Base, TimestampMixin, UserRole

if TYPE_CHECKING:
    from omnix.db.models.organization import Organization
    from omnix.db.models.approval import Approval


class User(TimestampMixin, Base):
    """
    Platform user belonging to an organization.
    Only ADMIN and MANAGER roles can approve purchase orders.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Password hash placeholder — proper hashing added in auth phase
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), nullable=False, default=UserRole.STAFF
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="approved_by_user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role={self.role}>"
