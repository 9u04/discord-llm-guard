# Discord LLM Guard Bot

一个基于 LLM 的 Discord 垃圾消息审查 Bot，支持引用举报、自动分析与封禁/驳回/人工介入的完整流程，并提供轻量级控制台页面查看状态与历史记录。

## 核心功能
- 🎯 引用消息并 `@Bot` + 附言发起举报
- 🔍 自动拉取被举报用户资料与最近历史消息
- 🤖 LLM 分析后给出三类结论：`BAN` / `INVALID_REPORT` / `NEED_GM`
- ⚙️ 自动执行封禁、驳回或提醒 GM
- 📊 处理结果与日志落库，前端控制台可查询

## 工作流程
```
用户引用消息 @Bot 说明
         ↓
Bot 解析举报 + 收集用户信息
         ↓
LLM 分析（返回 JSON）
         ↓
执行动作并回复举报人
         ↓
日志落库 → 控制台查询
```

## 技术栈
| 组件 | 选择 | 说明 |
|------|------|------|
| 语言/框架 | Python 3.11 + discord.py 2.x | Discord Bot 框架 |
| 数据库 ORM | SQLAlchemy 2.0 | 多数据库支持 |
| 数据库引擎 | SQLite (本地) / PostgreSQL (生产) | Railway 免费 PostgreSQL |
| LLM | OpenAI 兼容 API | 支持中转站 |
| 控制台 API | FastAPI | 状态与历史查询 |
| 部署 | Docker + Railway | 容器化上云 |

## 目录结构
```
discord-llm-guard/
├── src/
│   ├── main.py                      # 入口文件
│   ├── bot/
│   │   ├── client.py                # Bot 客户端
│   │   └── events.py                # 事件处理
│   ├── services/
│   │   ├── discord_service.py       # Discord API 封装
│   │   ├── llm_service.py           # LLM 调用
│   │   └── moderation_service.py    # 审核逻辑
│   ├── database/
│   │   ├── models.py                # 数据模型
│   │   └── repository.py            # 数据访问
│   ├── prompts/
│   │   └── templates.py             # LLM 提示词
│   ├── config/
│   │   └── settings.py              # 配置管理
│   └── utils/
│       └── helpers.py               # 工具函数
├── frontend/                        # 控制台 Web 页面
├── data/                            # SQLite 数据库
├── Dockerfile                       # 容器镜像
├── railway.toml                     # Railway 配置
├── requirements.txt                 # Python 依赖
├── .env.example                     # 环境变量模板
└── PROGRESS.md                      # 开发进度
```

## 快速开始

### 前置条件
- Python 3.11+
- Discord Bot Token
- LLM API Key（OpenAI 或兼容服务）
- 可选：PostgreSQL（Railway 生产环境自动提供）

### 本地运行

**1. 克隆仓库并安装依赖**
```bash
git clone git@github.com:9u04/discord-llm-guard.git
cd discord-llm-guard
pip install -r requirements.txt
```

**2. 配置环境变量**
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env，填写必需配置
```

**3. 启动 Bot**
```bash
python -m src.main
```

Bot 启动后会在控制台打印状态。同时会启动 FastAPI 控制台服务（默认 `http://localhost:8000`）。

## 环境变量配置

### 必需配置
```env
# === Discord 配置 ===
DISCORD_TOKEN=your_bot_token_here
# 获取方式：https://discord.com/developers/applications
# 需要 Intents: Message Content, Server Members
# 权限：Send Messages, Ban Members, Delete Messages, Manage Messages

DISCORD_GM_ROLE_ID=123456789012345678
# GM 角色 ID（人工审核时会 @mention 此角色）
# 获取方式：右键点击 Discord 角色，复制 ID（需开启开发者模式）

# === LLM 配置 ===
LLM_API_KEY=sk-xxxxxxxxxxxx
# OpenAI API Key 或兼容服务密钥

LLM_BASE_URL=https://api.openai.com/v1
# LLM API 地址（支持中转站，如 https://api.deepseek.com/v1）

LLM_MODEL=gpt-4o
# 模型名称（推荐 gpt-4o、gpt-4-turbo）
```

### 可选配置
```env
# === 数据库 ===
DATABASE_URL=sqlite:///./data/bot.db
# 本地开发用 SQLite，Railway 生产会自动覆盖为 PostgreSQL
# 格式：sqlite:///./data/bot.db 或 postgresql://user:pass@host/db

# === 审核参数 ===
HISTORY_MESSAGE_LIMIT=10
# 拉取被举报用户的最近消息数（默认 10）

BAN_DELETE_DAYS=7
# 执行封禁时删除多少天内的消息（默认 7）

# === 控制台配置 ===
CONSOLE_USERNAME=admin
# 控制台登录账号（可选，默认无密保）

CONSOLE_PASSWORD=your_password
# 控制台登录密码

CONSOLE_APP_TITLE=Discord LLM Guard 控制台
# 控制台页面标题
```

## 测试与开发

**⚠️ 重要**：`testing/` 目录下的测试工具仅供本地开发使用，**不包含在部署包中**。

### 配置验证
```bash
# 快速检查 .env 文件格式与必需字段
python testing/tools/test_bot_quick.py
```

### 连接测试
```bash
# 测试 Discord Bot 连接与 token 有效性
python testing/tools/test_bot_enhanced.py

# 标准连接测试
python testing/tools/test_bot_connection.py
```

### LLM 测试
```bash
# 验证 LLM API 与 Prompt 解析
# 会生成本地测试数据库 testing/data/llm_real_test.db
python testing/scripts/llm_real_test.py
```

### 开发文档
- `BOT_MESSAGE_FLOW.md`：详细消息流程与状态图
- `testing/docs/TESTING_RESULTS.md`：测试结果汇总
- `PROGRESS.md`：开发进度与技术细节

## 控制台页面

Bot 启动后会同时启动控制台 API 服务，访问 `http://localhost:8000` 即可进入控制台（本地开发无需登录）。

### 功能
- 📊 **服务状态**：Bot 与数据库连接状态、最后心跳时间
- 📋 **处理历史**：所有举报记录、LLM 分析结果、执行动作
- 🔍 **详情查看**：被举报消息、用户历史消息、LLM 分析理由

### 本地登录配置
编辑 `frontend/config.local.js`（推荐创建此文件并加入 `.gitignore`）：
```javascript
window.APP_CONFIG_OVERRIDE = {
  auth: {
    username: "admin",
    password: "your_password_here",
  },
  // 若不是 localhost:8000，需配置 API 地址
  // apiBaseUrl: "http://your-api-server:8000",
};
```

## Railway 部署

### 部署步骤
1. **连接仓库**  
   Railway Dashboard → New Project → GitHub Repo

2. **添加 PostgreSQL**  
   Project Settings → Add Plugins → PostgreSQL  
   （Railway 会自动生成 `DATABASE_URL` 环境变量）

3. **配置环境变量**  
   Project Settings → Variables，填写：
   - `DISCORD_TOKEN`
   - `DISCORD_GM_ROLE_ID`
   - `LLM_API_KEY`
   - `LLM_BASE_URL`（可选）
   - `LLM_MODEL`（可选）
   - `CONSOLE_USERNAME`（可选）
   - `CONSOLE_PASSWORD`（可选）

4. **部署**  
   提交到 GitHub 后，Railway 自动构建并运行

### 生产环境特性
- 数据持久化：PostgreSQL 自动管理
- 日志：Railway 控制台可查看
- 自动重启：崩溃时自动恢复
- 域名：Railway 分配 Web URL

## 常见问题

**Q: Bot 无法连接？**  
A: 检查 `DISCORD_TOKEN` 是否正确，验证 Bot 的 Intents 权限（需要 Message Content Intent）。

**Q: LLM 返回不是 JSON？**  
A: Bot 会尝试关键词解析（BAN/INVALID/NEED），最后降级为人工介入。

**Q: 数据库连接错误？**  
A: 本地确认 `data/` 目录存在且可写；Railway 上确认 PostgreSQL 插件已添加。

**Q: 控制台打不开？**  
A: 确认 FastAPI 已启动（日志会有 `Uvicorn running on` 提示），访问 `http://localhost:8000`。

## 反馈与贡献
如有问题或建议，欢迎提交 Issue 或 PR！

## 许可证
MIT
