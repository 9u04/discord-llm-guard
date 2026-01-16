## Bot 被 @ 时的消息流程

### 📊 完整的数据流向图

```
Discord 频道中的用户行为
         ↓
    用户引用消息 + @ Bot + 附言
    例如: "@Bot 这是杀猪盘"
         ↓
Discord API 接收到消息
         ↓
    ┌─────────────────────────────────────┐
    │  Bot Client (discord.py)             │
    │  接收消息事件                        │
    │  on_message() 事件触发              │
    └─────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────┐
    │  事件处理层 (events.py)              │
    │  1. 检查消息是否 @Bot               │
    │  2. 验证消息格式（引用消息）        │
    │  3. 提取关键信息                    │
    │     - 举报人                       │
    │     - 被举报用户                   │
    │     - 被举报消息内容               │
    │     - 举报附言                     │
    └─────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────┐
    │  业务逻辑层 (moderation_service.py)  │
    │  1. 调用 Discord Service 获取数据    │
    │     - 被举报用户的账户信息         │
    │     - 用户最近的历史消息           │
    │     - 频道信息等                   │
    │  2. 构建 LLM 分析请求               │
    │  3. 调用 LLM Service               │
    └─────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────┐
    │  外部 API 调用                       │
    │  1. LLM Service 调用 OpenAI/中转     │
    │  2. 接收分析结果                    │
    │     - BAN                          │
    │     - INVALID_REPORT               │
    │     - NEED_GM                      │
    └─────────────────────────────────────┘
         ↓
    ┌─────────────────────────────────────┐
    │  执行动作 (Discord Service)          │
    │  根据 LLM 结果：                     │
    │  • BAN: 封禁 + 删除消息 + 回复      │
    │  • INVALID: 回复"未发现违规"       │
    │  • NEED_GM: @GM 角色 + 通知          │
    └─────────────────────────────────────┘
         ↓
    Discord API 执行操作 + 发送回复
         ↓
    用户看到 Bot 的回复与对应的动作
```

---

## 🔌 Discord.py 事件推送机制

### 1. **Bot 接收消息事件**

```python
# 在 bot/client.py 或 events.py 中
@bot.event
async def on_message(message):
    """
    Discord 推送消息事件时调用
    这是最基础的事件处理
    """
    # 检查是否是 Bot 自己的消息（避免自己回复自己）
    if message.author == bot.user:
        return
    
    # 检查消息是否 @Bot
    if bot.user in message.mentions:
        # 处理逻辑
        await handle_bot_mention(message)
```

### 2. **discord.py 的事件推送原理**

```
Discord WebSocket 连接
    ↓
接收事件 JSON（如 MESSAGE_CREATE）
    ↓
discord.py 解析 JSON
    ↓
创建 Message 对象
    ↓
调用注册的 @bot.event 函数
    ↓
你的代码执行
```

**关键点：**
- discord.py 使用 WebSocket 长连接接收事件
- 所有事件都是**异步的**（async/await）
- 事件推送**自动且实时**，无需轮询

---

## 🎯 具体实现流程

### 第一步：接收消息事件（discord.py 自动处理）

```python
# src/bot/client.py 中添加事件处理器
@bot.event
async def on_message(message: discord.Message):
    """Called when a message is sent in any channel the bot can see."""
    
    # 1. 忽略 Bot 自己的消息
    if message.author == bot.user:
        return
    
    # 2. 检查 Bot 是否被 @
    if bot.user not in message.mentions:
        return
    
    # 3. 检查是否是引用消息（回复消息）
    if message.reference is None:
        await message.reply("请通过引用消息来举报，例如：\n`@Bot 这是杀猪盘`")
        return
    
    # 4. 获取被引用的原始消息
    try:
        referenced_message = await message.channel.fetch_message(
            message.reference.message_id
        )
    except discord.NotFound:
        await message.reply("无法找到被引用的消息")
        return
    
    # 5. 准备举报信息
    report_info = {
        "reporter": message.author,           # 举报人
        "reported_user": referenced_message.author,  # 被举报用户
        "reported_message": referenced_message,      # 被举报消息
        "reason": message.content,            # 举报附言
        "channel": message.channel,
        "guild": message.guild,
    }
    
    # 6. 推送给后端处理
    await handle_report(report_info)
```

### 第二步：后端处理举报（业务逻辑层）

```python
# src/services/moderation_service.py
async def handle_report(report_info: dict):
    """处理用户举报"""
    
    # 1. 收集被举报用户的信息
    user_info = await discord_service.get_user_info(
        report_info["reported_user"]
    )
    
    # 2. 获取用户最近的消息历史
    user_history = await discord_service.get_user_message_history(
        report_info["channel"],
        report_info["reported_user"],
        limit=10
    )
    
    # 3. 构建 LLM 分析请求
    analysis_prompt = build_analysis_prompt(
        reported_message=report_info["reported_message"],
        user_history=user_history,
        user_info=user_info,
        report_reason=report_info["reason"]
    )
    
    # 4. 调用 LLM 进行分析
    result = await llm_service.analyze_message(analysis_prompt)
    
    # 5. 根据结果执行对应动作
    if result == "BAN":
        await execute_ban(report_info)
    elif result == "INVALID_REPORT":
        await execute_invalid(report_info)
    elif result == "NEED_GM":
        await escalate_to_gm(report_info)
```

### 第三步：执行动作（Discord API 调用）

```python
# src/services/discord_service.py
async def execute_ban(report_info):
    """封禁用户"""
    
    user_to_ban = report_info["reported_user"]
    guild = report_info["guild"]
    channel = report_info["channel"]
    
    # 1. 删除该用户 7 天内的消息
    async for message in channel.history(limit=None):
        if message.author == user_to_ban:
            if (datetime.utcnow() - message.created_at).days <= 7:
                await message.delete()
    
    # 2. 封禁用户
    await guild.ban(
        user_to_ban,
        reason="LLM Guard Bot 自动封禁"
    )
    
    # 3. 向举报人回复
    await channel.send(
        f"{report_info['reporter'].mention} "
        f"已处理该举报，用户已被封禁"
    )
```

---

## 🔑 关键技术点

### 1. **事件触发机制**

| 事件 | 何时触发 | 用途 |
|-----|--------|------|
| `on_message()` | 收到新消息 | 检测 @Bot |
| `on_ready()` | Bot 连接成功 | 初始化 |
| `on_member_join()` | 用户加入服务器 | 可用于审核新成员 |
| `on_member_remove()` | 用户离开服务器 | 清理数据 |

### 2. **异步非阻塞**

所有操作都是**异步的**，Bot 可以同时处理多个用户的举报：

```python
# ✅ 正确的异步处理
async def on_message(message):
    await asyncio.gather(
        handle_report_1(),
        handle_report_2(),
        handle_report_3(),
        # ... 可以同时处理多个任务
    )
```

### 3. **消息对象结构**

```python
message.author          # 发送人
message.content         # 消息文本
message.mentions        # @的用户列表
message.reference       # 引用信息（如果是回复）
message.channel         # 频道对象
message.guild           # 服务器对象
message.created_at      # 创建时间
```

---

## 📈 性能与可扩展性

### 推送机制的优势

✅ **实时性**：WebSocket 长连接，毫秒级响应  
✅ **效率**：不需要轮询 API  
✅ **可扩展**：discord.py 可以处理数千个并发消息  
✅ **自动重连**：Discord 连接断开时自动重新连接  

### 示例：并发处理多个举报

```python
# discord.py 自动为每条消息创建独立的任务
# 5 个用户同时 @ Bot，5 个 on_message() 会并发执行

@bot.event
async def on_message(message):
    # 每个消息都会触发这个函数
    # discord.py 内部使用 asyncio 管理并发
    await handle_report(message)
    # 处理不会阻塞其他消息的处理
```

---

## 🚀 总结

**Bot 被 @ 时的推送流程：**

1. 用户在 Discord 发送消息并 @Bot
2. Discord 服务器通过 WebSocket 推送事件给 Bot
3. discord.py 解析事件并调用 `on_message()` 函数
4. 你的代码检查是否是有效的举报请求
5. 调用后端服务进行分析
6. 执行对应的动作（封禁/驳回/通知 GM）
7. 用户看到 Bot 的回复和对应动作

**关键特点：**
- ✅ 实时推送，无需轮询
- ✅ 异步处理，可并发处理多个举报
- ✅ 完全由 discord.py 库自动管理
- ✅ 开发者只需实现业务逻辑




