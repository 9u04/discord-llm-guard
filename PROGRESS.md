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
| 二 | 核心服务实现 | Discord 服务、LLM 服务、审核服务、Prompt 模板 |
| 三 | 事件处理和动作执行 | 消息监听、命令解析、执行封禁/回复 |
| 四 | 数据库和日志 | SQLAlchemy ORM 集成、审核日志记录、错误处理 |
| 五 | 部署和文档 | Dockerfile 完善、Railway 部署测试、使用文档 |

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
- 2026-01-15

## 修改内容
- 初始化项目结构与基础文件
- 添加配置管理、Bot 客户端与入口文件骨架
- 添加部署配置与基础文档

## 当前进度
- 阶段一：基础框架（✅ 完成）
- 待办：阶段二核心服务、阶段三事件处理、阶段四数据库与日志、阶段五部署与文档
- 已推送到 GitHub：git@github.com:9u04/discord-llm-guard.git

## 上下文快照
- 采用 Python + discord.py + SQLAlchemy ORM
- 本地开发：SQLite 文件数据库
- Railway 生产：PostgreSQL（Railway 免费插件，自动生成 DATABASE_URL）
- LLM 接口兼容 OpenAI
- 目录结构已预留 bot/services/database/prompts/config/utils 等模块

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

