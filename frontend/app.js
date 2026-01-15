import { APP_CONFIG, applyConfigOverride } from "./config.js";
import { MOCK_REPORTS, MOCK_STATUS } from "./mock-data.js";

const AUTH_STORAGE_KEY = "llm-guard-auth";
const root = document.getElementById("app");

const state = {
  status: null,
  reports: [],
  statusSource: "mock",
  reportsSource: "mock",
  isLoading: false,
  selectedReportIndex: null,
  lastFetchedAt: null,
};

const formatDate = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
};

const getBadge = (value) => {
  if (value === true || value === "ONLINE" || value === "DONE") {
    return { label: "正常", tone: "ok" };
  }
  if (value === false || value === "OFFLINE" || value === "FAILED") {
    return { label: "异常", tone: "err" };
  }
  return { label: value || "未知", tone: "warn" };
};

const getResultBadge = (decision) => {
  if (decision === "BAN") {
    return { label: "BAN", tone: "err" };
  }
  if (decision === "NEED_GM") {
    return { label: "需要GM", tone: "warn" };
  }
  if (decision === "INVALID_REPORT") {
    return { label: "无需处理", tone: "ok" };
  }
  return { label: decision || "未知", tone: "warn" };
};

const normalizeHistory = (value) => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
};

const getApiUrl = (path) => {
  const base = APP_CONFIG.apiBaseUrl?.trim();
  if (!base) return path;
  return `${base.replace(/\/$/, "")}${path}`;
};

const fetchJson = async (path, fallback) => {
  try {
    const response = await fetch(getApiUrl(path), {
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return { data: await response.json(), source: "api" };
  } catch (error) {
    return { data: fallback, source: "mock" };
  }
};

const isAuthed = () => sessionStorage.getItem(AUTH_STORAGE_KEY) === "1";

const setAuthed = (value) => {
  if (value) {
    sessionStorage.setItem(AUTH_STORAGE_KEY, "1");
  } else {
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
  }
};

const renderLogin = () => {
  root.innerHTML = `
    <div class="card login">
      <h1>${APP_CONFIG.appTitle}</h1>
      <p class="muted">请输入配置的账号密码（后续将接入 Discord OAuth）。</p>
      <form id="login-form">
        <div class="field">
          <label for="username">账号</label>
          <input id="username" type="text" placeholder="输入账号" autocomplete="username" />
        </div>
        <div class="field">
          <label for="password">密码</label>
          <input id="password" type="password" placeholder="输入密码" autocomplete="current-password" />
        </div>
        <div class="actions">
          <span class="muted" id="login-error"></span>
          <button class="button" type="submit">登录</button>
        </div>
      </form>
    </div>
  `;

  const form = document.getElementById("login-form");
  const errorEl = document.getElementById("login-error");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    if (
      username === APP_CONFIG.auth.username &&
      password === APP_CONFIG.auth.password
    ) {
      setAuthed(true);
      render();
      return;
    }
    errorEl.textContent = "账号或密码错误";
  });
};

const renderDashboard = () => {
  root.innerHTML = `
    <div class="header">
      <div>
        <div class="title">${APP_CONFIG.appTitle}</div>
        <div class="muted">服务状态与处理历史</div>
        <div class="muted" id="fetch-time">数据拉取时间：-</div>
      </div>
      <div class="toolbar">
        <button class="button secondary" id="refresh-btn">刷新</button>
        <button class="button" id="logout-btn">退出</button>
      </div>
    </div>

    <div class="grid two">
      <div class="card compact" id="status-card">
        <h3>服务状态</h3>
        <div class="muted">加载中...</div>
      </div>
      <div class="card compact" id="summary-card">
        <h3>处理概览</h3>
        <div id="summary" class="muted">加载中...</div>
      </div>
    </div>

    <div class="card" style="margin-top: 20px;">
      <div class="header" style="margin-bottom: 12px;">
        <div>
          <h3>处理历史</h3>
          <div class="muted">最近 20 条记录</div>
        </div>
      </div>
      <div id="history-list"></div>
    </div>
  `;

  document.getElementById("logout-btn").addEventListener("click", () => {
    setAuthed(false);
    render();
  });
  document.getElementById("refresh-btn").addEventListener("click", () => {
    loadDashboard();
  });
  loadDashboard();
};

const renderStatus = () => {
  const container = document.getElementById("status-card");
  if (!state.status) {
    container.innerHTML = `<h3>服务状态</h3><div class="muted">暂无数据</div>`;
    return;
  }
  const botBadge = getBadge(state.status.bot_online);
  const dbBadge = getBadge(state.status.db_connected);
  container.innerHTML = `
    <div class="status-header">
      <h3>服务状态</h3>
      <div class="status-badges">
        <span class="badge ${botBadge.tone}">Bot ${botBadge.label}</span>
        <span class="badge ${dbBadge.tone}">数据库 ${dbBadge.label}</span>
      </div>
    </div>
    <div class="muted">队列待处理：${state.status.queue_depth ?? "-"}</div>
    <div class="muted">服务中的服务器：${state.status.active_guilds ?? "-"}</div>
  `;
};

const renderSummary = () => {
  const summaryEl = document.getElementById("summary");
  const total = state.reports.length;
  const banCount = state.reports.filter(
    (item) => item.llm_decision === "BAN"
  ).length;
  const invalidCount = state.reports.filter(
    (item) => item.llm_decision === "INVALID_REPORT"
  ).length;
  const gmCount = state.reports.filter(
    (item) => item.llm_decision === "NEED_GM"
  ).length;
  summaryEl.innerHTML = `
    <div class="muted">总记录：${total}</div>
    <div class="muted">封禁数：${banCount} / 放行数：${invalidCount} / 人工介入数：${gmCount}</div>
  `;
};

const renderHistory = () => {
  const container = document.getElementById("history-list");
  if (!state.reports.length) {
    container.innerHTML = `<div class="empty">暂无历史记录</div>`;
    return;
  }
  container.innerHTML = `
    <table class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>时间</th>
          <th>举报人</th>
          <th>被举报人</th>
          <th>举报附言（原因）</th>
          <th>处理结果</th>
        </tr>
      </thead>
      <tbody>
        ${state.reports
          .map((item, index) => {
            const resultBadge = getResultBadge(item.llm_decision);
            const isSelected = state.selectedReportIndex === index;
            return `
              <tr class="report-row ${isSelected ? "is-selected" : ""}" data-report-index="${index}">
                <td>${item.id ?? "-"}</td>
                <td>${formatDate(item.created_at)}</td>
                <td>${item.reporter_name ?? "-"}</td>
                <td>${item.reported_user_name ?? "-"}</td>
                <td>${item.report_reason ?? "-"}</td>
                <td><span class="result-badge ${resultBadge.tone}">${resultBadge.label}</span></td>
              </tr>
            `;
          })
          .join("")}
      </tbody>
    </table>
    <div id="report-detail" class="detail-panel"></div>
  `;

  document.querySelectorAll(".report-row").forEach((row) => {
    row.addEventListener("click", () => {
      const index = Number(row.dataset.reportIndex);
      if (Number.isNaN(index)) return;
      state.selectedReportIndex =
        state.selectedReportIndex === index ? null : index;
      renderHistory();
    });
  });

  renderReportDetail();
};

const renderReportDetail = () => {
  const detailEl = document.getElementById("report-detail");
  if (!detailEl) return;
  if (state.selectedReportIndex === null) {
    detailEl.innerHTML = `<div class="muted">点击记录查看详情</div>`;
    return;
  }
  const report = state.reports[state.selectedReportIndex];
  if (!report) {
    detailEl.innerHTML = `<div class="muted">未找到对应记录</div>`;
    return;
  }
  const historyItems = normalizeHistory(report.reported_user_history);
  const historyHtml = historyItems.length
    ? `<ul class="history-list">
        ${historyItems
          .map(
            (item) =>
              `<li><span class="muted">${formatDate(
                item.created_at
              )}</span> ${item.content || "(空消息)"}</li>`
          )
          .join("")}
      </ul>`
    : `<div class="muted">暂无历史消息</div>`;
  const resultBadge = getResultBadge(report.llm_decision);

  detailEl.innerHTML = `
    <div class="detail-header">
      <div>
        <strong>详情</strong>
        <span class="muted">#${report.id ?? "-"}</span>
      </div>
      <span class="result-badge ${resultBadge.tone}">${resultBadge.label}</span>
    </div>
    <div class="detail-grid">
      <div>
        <div class="detail-label">被举报消息</div>
        <div class="detail-content">${report.reported_message_content ?? "-"}</div>
        ${
          report.reported_message_url
            ? `<a class="detail-link" href="${report.reported_message_url}" target="_blank">跳转消息</a>`
            : ""
        }
      </div>
      <div>
        <div class="detail-label">举报附言</div>
        <div class="detail-content">${report.report_reason ?? "-"}</div>
      </div>
      <div>
        <div class="detail-label">LLM 分析</div>
        <div class="detail-content">${report.llm_reasoning ?? "-"}</div>
        <div class="muted">置信度：${report.llm_confidence ?? "-"}</div>
      </div>
    </div>
    <div class="detail-label" style="margin-top: 12px;">被举报历史消息</div>
    ${historyHtml}
  `;
};

const renderFetchTime = () => {
  const el = document.getElementById("fetch-time");
  if (!el) return;
  el.textContent = `数据拉取时间：${formatDate(state.lastFetchedAt)}`;
};

const loadDashboard = async () => {
  if (state.isLoading) return;
  state.isLoading = true;
  const refreshBtn = document.getElementById("refresh-btn");
  if (refreshBtn) refreshBtn.disabled = true;

  const statusResult = await fetchJson("/api/status", MOCK_STATUS);
  const reportsResult = await fetchJson("/api/reports?limit=20", MOCK_REPORTS);
  state.status = statusResult.data;
  state.reports = Array.isArray(reportsResult.data)
    ? reportsResult.data
    : reportsResult.data?.items ?? [];
  state.statusSource = statusResult.source;
  state.reportsSource = reportsResult.source;
  state.lastFetchedAt = new Date().toISOString();
  renderStatus();
  renderSummary();
  renderHistory();
  renderFetchTime();
  state.isLoading = false;
  if (refreshBtn) refreshBtn.disabled = false;
};

const loadRuntimeConfig = async () => {
  try {
    const response = await fetch("/api/config", {
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) return;
    const data = await response.json();
    if (!data || typeof data !== "object") return;
    const hasAuth =
      data.auth &&
      (typeof data.auth.username === "string" ||
        typeof data.auth.password === "string");
    if (!hasAuth && !data.apiBaseUrl && !data.appTitle) return;
    applyConfigOverride({
      appTitle: data.appTitle,
      apiBaseUrl: data.apiBaseUrl,
      auth: data.auth,
    });
  } catch (error) {
    // Ignore runtime config errors and keep defaults.
  }
};

const render = () => {
  if (isAuthed()) {
    renderDashboard();
  } else {
    renderLogin();
  }
};

const bootstrap = async () => {
  if (typeof window !== "undefined" && window.APP_CONFIG_OVERRIDE) {
    applyConfigOverride(window.APP_CONFIG_OVERRIDE);
  }
  await loadRuntimeConfig();
  render();
};

bootstrap();

