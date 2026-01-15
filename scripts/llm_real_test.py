"""Run real LLM tests and store results in local SQLite."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.prompts.templates import build_analysis_prompt
from src.services.llm_service import LLMService

DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "llm_real_test.db"

TEST_CASES = [
    {
        "case_id": "case_ban_scam",
        "reported_message": "加我微信领红包，刷流水一天稳赚500。",
        "report_reason": "明显杀猪盘，引流诈骗",
        "user_info": {
            "id": 1001,
            "name": "new_user_01",
            "created_at": "2026-01-10T09:00:00+00:00",
            "joined_at": "2026-01-10T09:05:00+00:00",
            "is_bot": False,
            "roles": ["Member"],
        },
        "history": [
            {"content": "加微信咨询收益", "created_at": "2026-01-10T09:06:00+00:00"},
            {"content": "帮忙做任务返钱", "created_at": "2026-01-10T09:07:00+00:00"},
            {"content": "私聊发你资料", "created_at": "2026-01-10T09:08:00+00:00"},
        ],
    },
    {
        "case_id": "case_invalid_normal_chat",
        "reported_message": "大家晚上好，今天的会议纪要我发群里了。",
        "report_reason": "感觉他在刷屏",
        "user_info": {
            "id": 2002,
            "name": "regular_member",
            "created_at": "2024-06-01T12:00:00+00:00",
            "joined_at": "2024-06-02T12:00:00+00:00",
            "is_bot": False,
            "roles": ["Member", "Contributor"],
        },
        "history": [
            {"content": "我把文档链接放在公告了", "created_at": "2026-01-12T10:00:00+00:00"},
            {"content": "有问题在这里反馈", "created_at": "2026-01-12T10:02:00+00:00"},
            {"content": "谢谢大家", "created_at": "2026-01-12T10:05:00+00:00"},
        ],
    },
    {
        "case_id": "case_need_gm_ambiguous",
        "reported_message": "这个项目我可以帮忙推广，点这里了解 https://example.com",
        "report_reason": "疑似引流广告",
        "user_info": {
            "id": 3003,
            "name": "promo_user",
            "created_at": "2025-12-01T08:00:00+00:00",
            "joined_at": "2025-12-05T08:00:00+00:00",
            "is_bot": False,
            "roles": ["Member"],
        },
        "history": [
            {"content": "我有资源可合作", "created_at": "2026-01-13T09:00:00+00:00"},
            {"content": "有兴趣私信", "created_at": "2026-01-13T09:02:00+00:00"},
        ],
    },
]


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_test_cases (
            case_id TEXT PRIMARY KEY,
            reported_message TEXT NOT NULL,
            report_reason TEXT NOT NULL,
            user_info TEXT NOT NULL,
            history TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            confidence REAL NOT NULL,
            reasoning TEXT NOT NULL,
            prompt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(case_id) REFERENCES llm_test_cases(case_id)
        )
        """
    )
    conn.commit()


def upsert_case(conn: sqlite3.Connection, case: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT OR IGNORE INTO llm_test_cases (
            case_id, reported_message, report_reason, user_info, history, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            case["case_id"],
            case["reported_message"],
            case["report_reason"],
            str(case["user_info"]),
            str(case["history"]),
            now,
        ),
    )
    conn.commit()


def save_result(
    conn: sqlite3.Connection,
    case_id: str,
    decision: str,
    confidence: float,
    reasoning: str,
    prompt: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO llm_test_results (
            case_id, decision, confidence, reasoning, prompt, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (case_id, decision, confidence, reasoning, prompt, now),
    )
    conn.commit()


async def run_tests() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    llm_service = LLMService()

    for case in TEST_CASES:
        upsert_case(conn, case)
        prompt = build_analysis_prompt(
            reported_message_content=case["reported_message"],
            user_history=case["history"],
            user_info=case["user_info"],
            report_reason=case["report_reason"],
        )
        result = await llm_service.analyze_report(prompt)
        save_result(
            conn,
            case_id=case["case_id"],
            decision=result.decision.value,
            confidence=result.confidence,
            reasoning=result.reasoning,
            prompt=prompt,
        )
        print(
            f"[{case['case_id']}] decision={result.decision.value} "
            f"confidence={result.confidence:.2f} reasoning={result.reasoning}"
        )

    conn.close()
    print(f"\n✅ 测试完成，结果已写入 {DB_PATH}")


if __name__ == "__main__":
    asyncio.run(run_tests())

