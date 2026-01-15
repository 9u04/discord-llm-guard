"""Database repository."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.database.models import Base, BotStatus, ReportLog

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def _get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url
        engine_kwargs: dict = {"future": True}
        if db_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_recycle"] = 300
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 10
        _engine = create_engine(db_url, **engine_kwargs)
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)
    return _engine


def check_db_connection() -> bool:
    """Check database connectivity."""
    try:
        engine = _get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def init_db() -> None:
    """Initialize database tables."""
    engine = _get_engine()
    Base.metadata.create_all(engine)
    _ensure_report_log_bigint(engine)
    _ensure_report_log_history(engine)


def _ensure_report_log_bigint(engine) -> None:
    if engine.dialect.name != "postgresql":
        return
    alter_statements = (
        "ALTER TABLE report_logs ALTER COLUMN guild_id TYPE BIGINT",
        "ALTER TABLE report_logs ALTER COLUMN channel_id TYPE BIGINT",
        "ALTER TABLE report_logs ALTER COLUMN reporter_id TYPE BIGINT",
        "ALTER TABLE report_logs ALTER COLUMN reported_user_id TYPE BIGINT",
        "ALTER TABLE report_logs ALTER COLUMN reported_message_id TYPE BIGINT",
    )
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                # Ignore when table/column does not exist yet or type is already BIGINT.
                continue


def _ensure_report_log_history(engine) -> None:
    statements = []
    if engine.dialect.name == "postgresql":
        statements.append(
            "ALTER TABLE report_logs ADD COLUMN IF NOT EXISTS reported_user_history TEXT"
        )
    else:
        statements.append("ALTER TABLE report_logs ADD COLUMN reported_user_history TEXT")
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                # Ignore if column already exists or table not created yet.
                continue


@contextmanager
def get_session() -> Session:
    """Provide a transactional session."""
    if _SessionLocal is None:
        _get_engine()
    assert _SessionLocal is not None
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class ReportRepository:
    """Repository for report logs."""

    def create_report(self, session: Session, report: ReportLog) -> int:
        session.add(report)
        session.flush()
        return report.id

    def update_llm_result(
        self,
        session: Session,
        report_id: int,
        decision: str,
        confidence: float,
        reasoning: str,
    ) -> None:
        stmt = select(ReportLog).where(ReportLog.id == report_id)
        report = session.scalar(stmt)
        if report is None:
            return
        report.llm_decision = decision
        report.llm_confidence = confidence
        report.llm_reasoning = reasoning
        report.status = "LLM_DONE"

    def update_action_result(
        self,
        session: Session,
        report_id: int,
        action_taken: str,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        stmt = select(ReportLog).where(ReportLog.id == report_id)
        report = session.scalar(stmt)
        if report is None:
            return
        report.action_taken = action_taken
        report.action_success = success
        report.error_message = error_message
        report.status = "DONE" if success else "FAILED"
        report.resolved_at = datetime.now(timezone.utc)

    def list_reports(self, session: Session, limit: int = 20) -> list[ReportLog]:
        stmt = select(ReportLog).order_by(ReportLog.created_at.desc()).limit(limit)
        return list(session.scalars(stmt).all())


class StatusRepository:
    """Repository for bot status heartbeat."""

    def upsert_status(
        self, session: Session, active_guilds: int, queue_depth: int | None
    ) -> None:
        status = session.get(BotStatus, 1)
        if status is None:
            status = BotStatus(
                id=1,
                active_guilds=active_guilds,
                queue_depth=queue_depth,
                last_heartbeat=datetime.now(timezone.utc),
            )
            session.add(status)
            return
        status.active_guilds = active_guilds
        status.queue_depth = queue_depth
        status.last_heartbeat = datetime.now(timezone.utc)

    def get_latest_status(self, session: Session) -> BotStatus | None:
        return session.get(BotStatus, 1)

    def is_online(self, status: BotStatus | None, ttl_seconds: int = 120) -> bool:
        if status is None:
            return False
        now = datetime.now(timezone.utc)
        return now - status.last_heartbeat <= timedelta(seconds=ttl_seconds)


