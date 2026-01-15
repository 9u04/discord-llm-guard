# Discord LLM Guard Bot

一个基于 LLM 的 Discord 垃圾消息审查 Bot。

## 功能概述
- 用户引用消息并 @Bot + 附言进行举报
- Bot 收集被举报者资料与历史消息，提交 LLM 分析
- 根据结果执行：封禁/驳回/通知 GM

## 本地运行
1. 复制 `.env.example` 为 `.env` 并填写配置
2. 安装依赖：`pip install -r requirements.txt`
3. 启动：`python -m src.main`

## Railway 部署
1. 连接仓库
2. 配置环境变量
3. 部署

