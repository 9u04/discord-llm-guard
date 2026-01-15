"""FastAPI app for console data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.database import get_session, init_db
from src.database.models import ReportLog
from src.database.repository import ReportRepository, StatusRepository, check_db_connection

app = FastAPI(title="Discord LLM Guard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def _serialize_report(report: ReportLog) -> dict[str, Any]:
    return {
        "id": report.id,
        "guild_id": report.guild_id,
        "channel_id": report.channel_id,
        "reporter_id": report.reporter_id,
        "reporter_name": report.reporter_name,
        "reported_user_id": report.reported_user_id,
        "reported_user_name": report.reported_user_name,
        "reported_message_id": report.reported_message_id,
        "reported_message_content": report.reported_message_content,
        "reported_message_url": report.reported_message_url,
        "report_reason": report.report_reason,
        "llm_decision": report.llm_decision,
        "llm_confidence": report.llm_confidence,
        "llm_reasoning": report.llm_reasoning,
        "action_taken": report.action_taken,
        "action_success": report.action_success,
        "error_message": report.error_message,
        "status": report.status,
        "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "updated_at": report.updated_at.isoformat() if report.updated_at else None,
    }


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    status_repo = StatusRepository()
    db_connected = check_db_connection()
    with get_session() as session:
        status = status_repo.get_latest_status(session)
    last_heartbeat = status.last_heartbeat if status else None
    return {
        "bot_online": status_repo.is_online(status),
        "db_connected": db_connected,
        "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None,
        "queue_depth": status.queue_depth if status else None,
        "active_guilds": status.active_guilds if status else None,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/reports")
def get_reports(limit: int = Query(default=20, ge=1, le=200)) -> list[dict[str, Any]]:
    repo = ReportRepository()
    with get_session() as session:
        reports = repo.list_reports(session, limit=limit)
    return [_serialize_report(report) for report in reports]


@app.get("/api/config")
def get_runtime_config() -> dict[str, Any]:
    settings = get_settings()
    payload: dict[str, Any] = {}
    if settings.console_app_title:
        payload["appTitle"] = settings.console_app_title
    if settings.console_api_base_url:
        payload["apiBaseUrl"] = settings.console_api_base_url
    if settings.console_username or settings.console_password:
        payload["auth"] = {
            "username": settings.console_username,
            "password": settings.console_password,
        }
    return payload

