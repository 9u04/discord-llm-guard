export const MOCK_STATUS = {
  bot_online: true,
  db_connected: true,
  last_heartbeat: "2026-01-15T10:20:30Z",
  queue_depth: 0,
  active_guilds: 1,
};

export const MOCK_REPORTS = [
  {
    id: 1024,
    reporter_name: "GM Stone",
    reported_user_name: "Stone助手",
    report_reason: "这是杀猪盘",
    llm_decision: "INVALID_REPORT",
    action_taken: "NONE",
    status: "DONE",
    created_at: "2026-01-15T09:58:12Z",
  },
  {
    id: 1023,
    reporter_name: "玩家A",
    reported_user_name: "陌生人X",
    report_reason: "疑似广告",
    llm_decision: "BAN",
    action_taken: "BAN",
    status: "DONE",
    created_at: "2026-01-15T09:40:48Z",
  },
  {
    id: 1022,
    reporter_name: "玩家B",
    reported_user_name: "新账号",
    report_reason: "不确定",
    llm_decision: "NEED_GM",
    action_taken: "ESCALATE",
    status: "FAILED",
    created_at: "2026-01-15T09:22:15Z",
  },
];

