"""Database models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class."""


class ReportLog(Base):
    """Report audit log."""

    __tablename__ = "report_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    reporter_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    reporter_name: Mapped[str | None] = mapped_column(String(64))
    reported_user_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    reported_user_name: Mapped[str | None] = mapped_column(String(64))
    reported_message_id: Mapped[int | None] = mapped_column(BigInteger)
    reported_message_content: Mapped[str | None] = mapped_column(Text)
    reported_message_url: Mapped[str | None] = mapped_column(Text)
    report_reason: Mapped[str | None] = mapped_column(Text)
    reported_user_history: Mapped[str | None] = mapped_column(Text)

    llm_decision: Mapped[str | None] = mapped_column(String(32))
    llm_confidence: Mapped[float | None] = mapped_column(Float)
    llm_reasoning: Mapped[str | None] = mapped_column(Text)

    action_taken: Mapped[str | None] = mapped_column(String(32))
    action_success: Mapped[bool | None] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BotStatus(Base):
    """Latest bot status heartbeat."""

    __tablename__ = "bot_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    active_guilds: Mapped[int | None] = mapped_column(Integer)
    queue_depth: Mapped[int | None] = mapped_column(Integer)

