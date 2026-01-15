# Discord LLM Guard Bot - 开发进度文档

## 项目概述

**功能需求：** Discord 垃圾消息审查 Bot，用户通过引用消息并 @Bot 发起举报，Bot 自动分析判定，执行对应动作。

**核心流程：**
1. 用户引用垃圾消息并 @Bot + 附言（如："@Bot 这是杀猪盘"）
2. Bot 收集信息：被举报消息内容 + 该用户最近 10 条历史消息 + 账号信息（注册时间、加入时间）
3. 送 LLM 分析，返回三类判定：
   - **BAN**：封禁用户 + 删除 7 天内消息 + 回复举报人
   - **INVALID_REPORT**：误报，回复举报人"未发现违规"
   - **NEED_GM**：不确定，@GM 角色 + 回复"这个我不好说，管理员你看看"
4. 所有结果在频道中可见回复，@举报人

## 技术栈

| 层级 | 技术选择 | 说明 |
|------|---------|------|
| 框架 | Python 3.11+ + discord.py 2.x | Discord Bot 框架 |
| LLM | OpenAI API（兼容中转站） | 消息分析和判定 |
| 数据库 ORM | SQLAlchemy 2.0+ | 统一 ORM，支持多种数据库 |
| 数据库引擎 | SQLite (开发) + PostgreSQL (Railway生产) | 本地开发用 SQLite，Railway 用 PostgreSQL（免费插件） |
| 配置 | pydantic + pydantic-settings + python-dotenv | 类型安全配置管理 |
| 部署 | Docker + Railway | 容器化部署 |

**数据库策略说明：**
- **本地开发**：`DATABASE_URL=sqlite:///./data/bot.db`（SQLite 文件）
- **Railway 生产**：`DATABASE_URL=postgresql://...`（由 Railway PostgreSQL 插件自动生成）
- **代码层统一**：使用 SQLAlchemy ORM，无缝切换，无需修改业务代码

## 架构设计

**系统架构：**
```
Discord → Bot Client → Event Handler → Command Parser → Moderation Service
                                                             ↓
                                          ┌─────────────────┼─────────────────┐
                                          ↓                 ↓                 ↓
                                    Discord Service    LLM Service      Database (SQLAlchemy)
                                          ↓                 ↓                 ↓
                                    Discord API         LLM API    SQLite(开发) / PostgreSQL(生产)
```

**核心模块解耦：**
- `bot/client.py` - Bot 客户端初始化
- `bot/events.py` - 消息事件监听和解析
- `services/discord_service.py` - Discord API 封装（获取用户信息、历史消息、执行封禁）
- `services/llm_service.py` - LLM 调用封装（分析请求、处理响应）
- `services/moderation_service.py` - 审核业务逻辑编排（流程控制、动作执行）
- `prompts/templates.py` - LLM Prompt 模板（分析提示词）
- `database/models.py` - 数据模型（SQLAlchemy ORM）
- `database/repository.py` - 数据访问层（CRUD 操作）
- `config/settings.py` - 配置管理（环境变量加载）

**目录结构：**
```
discord-llm-guard/
├── src/
│   ├── __init__.py
│   ├── main.py                      # 入口
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── client.py                # Bot 客户端
│   │   └── events.py                # 事件处理
│   ├── services/
│   │   ├── __init__.py
│   │   ├── discord_service.py       # Discord API 封装
│   │   ├── llm_service.py           # LLM 调用封装
│   │   └── moderation_service.py    # 审核业务逻辑
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # 数据模型
│   │   └── repository.py            # 数据访问层
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py             # Prompt 模板
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # 配置管理
│   └── utils/
│       ├── __init__.py
│       └── helpers.py               # 工具函数
├── data/                            # SQLite 数据库文件
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── railway.toml
├── README.md
└── PROGRESS.md
```

## 开发阶段规划

| 阶段 | 任务 | 预期交付 |
|------|------|---------|
| 一 | 基础框架搭建 | 目录结构、配置管理、Bot 客户端骨架 |
| 二 | Bot 核心部分开发 | 配置、事件处理、Discord 服务、LLM 服务（占位）、审核服务 |
| 三 | 事件处理和动作执行 | 消息监听完善、命令解析、执行封禁/回复 |
| 四 | 数据库和日志 | SQLAlchemy ORM 集成、审核日志记录、错误处理 |
| 五 | 部署和文档 | Dockerfile 完善、Railway 部署测试、使用文档 |

## Bot 开发详细规划（阶段二）

### 开发原则
**先调试 Bot 核心部分，再接入复杂的 LLM/数据库**

### 分层开发顺序

**第一层：Bot 客户端 + 基础事件处理**
```
src/config/settings.py        ← 配置管理（Discord/LLM/数据库）
    ↓
src/bot/client.py            ← Bot 客户端初始化
    ↓
src/bot/events.py            ← 消息事件监听、@mention 解析、引用消息提取
    ↓
src/main.py                  ← 启动 Bot
```
**目标**：Bot 能正常上线，正确解析 @mention + 引用消息

**第二层：Discord 服务（API 封装）**
```
src/services/discord_service.py
  ├── get_user_info()           # 获取用户ID、注册时间
  ├── get_member_info()         # 获取加入时间、角色
  ├── get_message_history()     # 获取用户最近10条消息
  ├── send_reply()              # 回复消息（支持@提及）
  └── ban_member()              # 执行封禁、删除消息
```
**目标**：能通过 Discord API 获取和操作数据

**第三层：LLM 服务（占位实现）**
```
src/services/llm_service.py
  ├── analyze_report()          # 分析举报（先返回模拟结果）
  └── 返回判定：BAN / INVALID_REPORT / NEED_GM
```
**目标**：完整流程能跑通，用模拟数据测试

**第四层：Prompt 模板**
```
src/prompts/templates.py
  └── 设计清晰的 Prompt，包含被举报消息、历史记录、账号信息
```
**目标**：LLM 能准确分析

**第五层：审核业务逻辑**
```
src/services/moderation_service.py
  ├── 流程编排：收集信息 → LLM 分析 → 执行动作
  ├── 动作执行：BAN / 驳回 / @GM
  └── 返回结果
```
**目标**：完整的审核流程运行

### 分阶段测试计划

**✅ 测试轮次 1（配置 + 事件处理）**
```bash
python -m src.main
# 在 Discord 频道：@Bot 发送消息（带引用）
# 验证：
#   - Bot 能上线
#   - 控制台打印解析结果（举报人、被举报人、附言）
```

**✅ 测试轮次 2（+ Discord 服务）**
```bash
# 在频道发起举报
# 验证：
#   - 获取用户信息正确
#   - 历史消息能取到
#   - 控制台打印信息完整
```

**✅ 测试轮次 3（+ LLM 服务占位）**
```bash
# 使用模拟 LLM 返回
# 验证：
#   - 完整流程能运行
#   - 根据模拟结果执行动作
#   - 回复消息格式正确
```

**✅ 测试轮次 4（+ 真实 LLM）**
```bash
# 使用真实 OpenAI API
# 验证：
#   - LLM 分析结果合理
#   - 三类判定正确处理
#   - 封禁/驳回/GM通知逻辑正确
```

### 开发文件清单

| 优先级 | 文件 | 功能 | 状态 |
|--------|------|------|------|
| P0 | src/config/settings.py | 配置管理 | 🟡 需更新 |
| P0 | src/bot/events.py | 事件处理 | 🔴 待开发 |
| P1 | src/services/discord_service.py | Discord API | 🔴 待开发 |
| P1 | src/services/llm_service.py | LLM 调用 | 🔴 待开发 |
| P2 | src/prompts/templates.py | Prompt 模板 | 🔴 待开发 |
| P2 | src/services/moderation_service.py | 审核逻辑 | 🔴 待开发 |
| P3 | src/database/models.py | 数据模型 | ⏸️ 暂不开发 |
| P3 | src/database/repository.py | 数据访问 | ⏸️ 暂不开发 |

## 环境变量配置

```env
# Discord
DISCORD_TOKEN=your_bot_token
DISCORD_GM_ROLE_ID=your_gm_role_id

# LLM
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1  # 支持中转站
LLM_MODEL=gpt-4o

# 可选
DATABASE_URL=sqlite:///./data/bot.db
HISTORY_MESSAGE_LIMIT=10
BAN_DELETE_DAYS=7
```

---

## 时间/版本
- 2026-01-15 (前端控制台初始搭建)
- 2026-01-15 (前端认证账号更新)
- 2026-01-15 (前端认证本地覆盖方案)
- 2026-01-15 (前端认证环境变量注入)
- 2026-01-15 (最终更新)
- 2026-01-15 (事件处理与核心服务骨架)
- 2026-01-15 (接入真实 LLM)
- 2026-01-15 (真实 LLM 测试数据库与脚本)
- 2026-01-15 (控制台 API 串联数据库)
- 2026-01-16 (修复举报日志落库字段类型)
- 2026-01-16 (控制台历史视图与详情增强)

## 修改内容
- ✅ **前端控制台雏形**：新增 `frontend/` 静态页面，包含登录、服务状态与处理历史视图
- ✅ **本地认证配置**：通过 `frontend/config.js` 配置账号密码，后续可替换为 Discord OAuth
- ✅ **数据源占位**：前端支持 `/api/status` 与 `/api/reports` 接口读取，失败时回退模拟数据
- ✅ **认证账号更新**：预置密码更新为 `sony_a1024`
- ✅ **认证本地覆盖**：新增 `frontend/config.local.js`（已加入忽略），支持本地覆盖账号密码避免仓库暴露
- ✅ **默认配置收敛**：`frontend/config.js` 默认不含密码，通过覆盖配置注入
- ✅ **环境变量注入**：新增 `frontend/api/config.js` 读取 Vercel 环境变量并注入前端
- ✅ **运行时加载**：前端启动时读取 `/api/config` 覆盖账号密码与 API Base URL
- ✅ **配置验证完成**：Discord Token 和 GM Role ID 已正确配置
- ✅ **连接测试通过**：创建了 `test_bot_quick.py` 和 `test_bot_enhanced.py` 用于快速验证
- ✅ **消息流程文档**：创建了完整的消息推送流程说明
  - `BOT_MESSAGE_FLOW.md` - 详细的流程图和说明
  - `BOT_MESSAGE_FLOW_CODE.py` - 完整的实现示例代码
- 初始化项目结构与基础文件
- 添加配置管理、Bot 客户端与入口文件骨架
- 添加部署配置与基础文档
- ✅ **事件处理上线**：实现 `@Bot + 引用消息` 的举报解析与校验
- ✅ **服务骨架完善**：新增 Discord/LLM/审核服务的最小可用流程
- ✅ **Prompt 模板**：生成 LLM 分析请求的基础模板
- ✅ **Prompt 强化**：补充“仅输出 JSON”约束
- ✅ **工具函数**：补充 bot mention 清理与默认举报理由
- ✅ **LLM 实际接入**：使用 OpenAI 兼容 SDK 调用真实 LLM
- ✅ **结果解析**：支持 JSON 解析与异常降级到 NEED_GM
- ✅ **真实 LLM 测试**：新增 `scripts/llm_real_test.py` 与本地测试数据库
- ✅ **JSON 输出保障**：LLM 调用优先使用 json_object 模式
- ✅ **解析兜底**：非 JSON 输出时尝试关键词判定
- ✅ **调试开关**：`LLM_DEBUG_RAW=1` 输出原始返回
- ✅ **字段兼容**：支持 `conclusion/reason` 等别名
- ✅ **数据库落库**：新增举报日志表与记录流程（Railway 内部 PostgreSQL）
- ✅ **DB 稳定性**：连接池参数与 SQLite 线程配置
- ✅ **DB 性能**：将阻塞写入切换为后台线程
- ✅ **控制台 API**：新增 FastAPI 接口 `/api/status` `/api/reports` `/api/config`
- ✅ **跨域支持**：控制台 API 开启 CORS 访问
- ✅ **状态心跳**：新增 `bot_status` 表并由 Bot 定时写入心跳
- ✅ **报告查询**：后台接口直连 `report_logs` 输出前端历史数据
- ✅ **控制台配置**：新增控制台标题/账号密码的运行时配置项
- ✅ **日志落库修复**：将举报日志相关 ID 字段改为 BIGINT，避免 PostgreSQL int4 溢出导致写入失败
- ✅ **兼容迁移**：初始化数据库时自动尝试将 `report_logs` 的关键 ID 列升级为 BIGINT
- ✅ **前端列表增强**：处理历史列调整为 ID/时间/举报人/被举报人/原因/处理结果，并支持点击行查看详情
- ✅ **详情补充**：新增举报历史消息与 LLM 分析展示，前端样式与交互优化
- ✅ **日志扩展字段**：后端新增 `reported_user_history` 字段并写入用户历史消息供前端展示

## 当前进度
- 阶段一：基础框架（✅ 完成）
  - ✅ 项目结构初始化
  - ✅ 环境配置验证
  - ✅ Bot 连接测试通过
- 阶段二：核心服务与事件处理（🟡 进行中）
  - ✅ 事件处理与举报校验
  - ✅ Discord/LLM/审核服务骨架
- ✅ 真实 LLM 接入与判定策略（基础）
- 阶段四：数据库与日志（🟡 进行中）
  - ✅ 举报日志表与落库流程
- 前端控制台（🟡 进行中）
  - ✅ 控制台 API 串联数据库
  - ✅ 登录与状态/历史页面雏形
  - ⏳ 等待对接 API 与 Discord OAuth
- 待办：阶段五部署与文档
- 已推送到 GitHub：git@github.com:9u04/discord-llm-guard.git

## 测试工具
| 工具 | 功能 | 用途 |
|-----|------|------|
| `test_bot_quick.py` | 快速配置验证 | 检查 .env 文件是否正确配置 token 和 role id |
| `test_bot_enhanced.py` | 详细连接测试 | 实际连接 Discord，验证 token 有效性和网络连接 |
| `test_bot_connection.py` | 标准连接测试 | 标准的连接验证脚本 |
| `scripts/llm_real_test.py` | 真实 LLM 测试 | 生成本地测试 DB 并验证 Prompt/解析 |

## 上下文快照
- 采用 Python + discord.py + SQLAlchemy ORM
- 本地开发：SQLite 文件数据库
- Railway 生产：PostgreSQL（Railway 免费插件，自动生成 DATABASE_URL）
- LLM 接口兼容 OpenAI
- 目录结构已预留 bot/services/database/prompts/config/utils 等模块
- 事件层已支持引用举报解析与基础错误提示
- 审核服务已串联 Discord 数据收集 → Prompt → LLM → 动作分发
- LLM 服务已接入真实 API，并要求 JSON 输出进行解析
- LLM 输出优先启用 json_object 模式，解析稳定性提升
- 非 JSON 输出时支持关键词兜底解析
- 已增加举报日志表字段，为后续前端状态/历史查询预留
- 数据库写入改为线程执行，避免阻塞 Bot 事件循环
- 新增 FastAPI 控制台 API，提供状态/历史接口
- Bot 会定时写入 `bot_status` 心跳，用于前端状态展示
- 已提供真实 LLM 测试脚本，默认写入 `data/llm_real_test.db`
- 已新增前端控制台静态页面，支持简单账号密码登录与状态/历史展示
- 前端支持通过 Vercel 环境变量注入默认账号密码
- PostgreSQL 已对 `report_logs` 的 Discord ID 字段做 BIGINT 兼容处理
- 处理历史支持点击查看举报消息、历史消息与 LLM 分析详情

## Railway 部署说明

**数据持久化方案：**
1. Railway 提供免费的 PostgreSQL 插件（无需额外配置）
2. 添加 PostgreSQL 后自动生成 `DATABASE_URL` 环境变量
3. Bot 启动时自动读取 `DATABASE_URL`，无缝切换至 PostgreSQL
4. 所有数据持久化存储在 PostgreSQL，容器重启不丢失数据

**Railway 部署步骤：**
1. 连接 GitHub 仓库到 Railway
2. 添加 PostgreSQL 插件（Railway Dashboard → Add Plugins）
3. 配置环境变量：`DISCORD_TOKEN`、`DISCORD_GM_ROLE_ID`、`LLM_API_KEY` 等
4. Railway 自动部署并监听 Bot

