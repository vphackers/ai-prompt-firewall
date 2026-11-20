
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    String,
    Text,
    DateTime,
    Identity,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PromptAuditLog(Base):
    __tablename__ = "prompt_audit_logs"

    __table_args__ = (
        CheckConstraint(
            "risk_status IN ('SAFE', 'BLOCKED', 'FLAGGED')",
            name="chk_risk_status"
        ),
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_risk_status", "risk_status"),
        Index("idx_audit_created_at",text("created_at DESC")),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            name="fk_prompt_user",
            ondelete="RESTRICT"
        ),
        nullable=False
    )

    raw_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    sanitized_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    risk_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    block_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ai_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
