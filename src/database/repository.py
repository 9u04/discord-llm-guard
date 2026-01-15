"""Database repository."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.database.models import Base, ReportLog

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


def init_db() -> None:
    """Initialize database tables."""
    engine = _get_engine()
    Base.metadata.create_all(engine)


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


