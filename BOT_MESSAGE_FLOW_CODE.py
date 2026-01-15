"""
Bot 被 @时的完整处理流程示例代码

这个文件展示了从接收 @Bot 消息到执行后端处理的完整流程
"""

import discord
from discord.ext import commands
from datetime import datetime


# ============================================================================
# 第一层：事件处理层 (bot/events.py)
# ============================================================================

async def setup_event_handlers(bot: commands.Bot):
    """注册 Bot 的事件处理器"""
    
    @bot.event
    async def on_message(message: discord.Message):
        """
        当 Discord 推送消息事件时调用
        
        流程：
        1. Discord → WebSocket → discord.py → on_message()
        2. 检查是否 @Bot
        3. 检查是否是有效的举报（引用消息）
        4. 推送给后端处理
        """
        
        # 1. 忽略 Bot 自己的消息
        if message.author == bot.user:
            return
        
        # 2. 忽略 DM（仅处理频道消息）
        if not isinstance(message.channel, discord.TextChannel):
            return
        
        # 3. 检查是否被 @
        if bot.user not in message.mentions:
            return
        
        print(f"[事件] Bot 被 @ 了!")
        print(f"  来自: {message.author.name}")
        print(f"  在频道: {message.channel.name}")
        print(f"  消息内容: {message.content}")
        
        # 4. 检查是否是引用消息（举报必须引用另一条消息）
        if message.reference is None:
            await message.reply(
                "❌ 请通过**引用消息**来举报\n"
                "操作方式：\n"
                "1. 右键点击要举报的消息\n"
                "2. 选择 '回复'\n"
                "3. 输入举报原因，例如：`@Bot 这是骗子`"
            )
            return
        
        print(f"[事件] 这是一个有效的举报请求")
        
        # 5. 获取被举报的原始消息
        try:
            reported_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            print(f"[事件] 被举报消息: {reported_message.content}")
        except discord.NotFound:
            await message.reply("❌ 无法找到被引用的消息")
            return
        except discord.Forbidden:
            await message.reply("❌ 没有权限访问该消息")
            return
        
        # 6. 检查被举报消息是否来自 Bot
        if reported_message.author == bot.user:
            await message.reply("❌ 不能举报 Bot 的消息")
            return
        
        # 7. 不能举报自己
        if reported_message.author == message.author:
            await message.reply("❌ 不能举报自己的消息")
            return
        
        # 8. 准备举报信息，推送给后端
        report_payload = {
            "reporter_id": message.author.id,
            "reporter_name": message.author.name,
            "reported_user_id": reported_message.author.id,
            "reported_user_name": reported_message.author.name,
            "reported_message_id": reported_message.id,
            "reported_message_content": reported_message.content,
            "report_reason": message.content.replace(f"<@{bot.user.id}>", "").strip(),
            "guild_id": message.guild.id,
            "guild_name": message.guild.name,
            "channel_id": message.channel.id,
            "channel_name": message.channel.name,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print(f"\n[推送] 将举报推送到后端服务")
        print(f"  举报人: {report_payload['reporter_name']}")
        print(f"  被举报人: {report_payload['reported_user_name']}")
        print(f"  举报原因: {report_payload['report_reason']}")
        
        # 9. 立即回复用户，告诉他们举报已收到
        await message.reply("✅ 已收到你的举报，正在处理中...")
        
        # 10. 调用后端服务处理举报
        await handle_report_backend(report_payload, message)


# ============================================================================
# 第二层：业务逻辑层 (services/moderation_service.py)
# ============================================================================

async def handle_report_backend(report_payload: dict, message: discord.Message):
    """
    处理举报的后端逻辑
    
    这个函数是真正的"后端"，接收事件层传来的数据
    进行分析和执行对应的动作
    """
    
    print(f"\n[后端] 开始处理举报")
    print(f"  数据包大小: {len(str(report_payload))} 字节")
    
    # 从 payload 提取信息
    guild = message.guild
    channel = message.channel
    reporter = message.author
    reported_user_id = report_payload["reported_user_id"]
    report_reason = report_payload["report_reason"]
    
    # 阶段 1: 数据收集
    print(f"\n[后端-阶段1] 收集数据...")
    
    # 1.1 获取被举报用户对象
    try:
        reported_user = guild.get_member(reported_user_id)
        if not reported_user:
            reported_user = await guild.fetch_member(reported_user_id)
    except discord.NotFound:
        await message.reply("❌ 无法找到被举报用户")
        return
    
    # 1.2 收集用户信息
    user_info = {
        "id": reported_user.id,
        "name": reported_user.name,
        "created_at": reported_user.created_at.isoformat(),
        "joined_at": reported_user.joined_at.isoformat() if reported_user.joined_at else None,
        "is_bot": reported_user.bot,
        "roles": [role.name for role in reported_user.roles],
    }
    print(f"  用户信息: {user_info['name']} (ID: {user_info['id']})")
    
    # 1.3 获取用户最近的消息历史
    user_message_history = []
    async for msg in channel.history(limit=50):
        if msg.author.id == reported_user_id:
            user_message_history.append({
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "url": msg.jump_url,
            })
        if len(user_message_history) >= 10:  # 只保留最近 10 条
            break
    
    print(f"  收集到 {len(user_message_history)} 条历史消息")
    
    # 阶段 2: LLM 分析（模拟）
    print(f"\n[后端-阶段2] 调用 LLM 分析...")
    
    # 这里会调用真实的 LLM 服务
    # llm_result = await llm_service.analyze_message(
    #     reported_message_content=report_payload["reported_message_content"],
    #     user_history=user_message_history,
    #     user_info=user_info,
    #     report_reason=report_reason
    # )
    
    # 为了演示，这里模拟 LLM 返回的结果
    llm_result = {
        "decision": "NEED_GM",  # BAN, INVALID_REPORT, or NEED_GM
        "confidence": 0.75,
        "reasoning": "可能存在不当言论，需要人工审核",
    }
    
    print(f"  LLM 决策: {llm_result['decision']}")
    print(f"  置信度: {llm_result['confidence']}")
    print(f"  原因: {llm_result['reasoning']}")
    
    # 阶段 3: 执行对应的动作
    print(f"\n[后端-阶段3] 执行动作...")
    
    if llm_result["decision"] == "BAN":
        await execute_ban(
            guild, channel, reported_user, reporter, report_payload
        )
    elif llm_result["decision"] == "INVALID_REPORT":
        await execute_invalid(channel, reporter, reported_user)
    elif llm_result["decision"] == "NEED_GM":
        await escalate_to_gm(guild, channel, reporter, reported_user, report_payload)
    
    print(f"\n[后端] 举报处理完成 ✅")


# ============================================================================
# 第三层：执行层 (services/discord_service.py)
# ============================================================================

async def execute_ban(
    guild: discord.Guild,
    channel: discord.TextChannel,
    reported_user: discord.Member,
    reporter: discord.User,
    report_payload: dict,
):
    """执行封禁动作"""
    
    print(f"\n  [执行] 开始封禁流程...")
    
    # 1. 删除用户 7 天内的消息
    delete_count = 0
    async for msg in channel.history(limit=None):
        if msg.author.id == reported_user.id:
            age_days = (datetime.utcnow() - msg.created_at).days
            if age_days <= 7:
                try:
                    await msg.delete()
                    delete_count += 1
                except discord.Forbidden:
                    print(f"  [执行] 没有权限删除消息: {msg.id}")
    
    print(f"  [执行] 已删除 {delete_count} 条消息")
    
    # 2. 封禁用户
    try:
        await guild.ban(
            reported_user,
            reason=f"LLM Guard 自动封禁 (举报人: {reporter.name}, 原因: {report_payload['report_reason']})"
        )
        print(f"  [执行] 用户 {reported_user.name} 已被封禁")
    except discord.Forbidden:
        print(f"  [执行] 没有权限封禁用户")
        return
    
    # 3. 在频道中发送通知
    embed = discord.Embed(
        title="✅ 违规用户已处理",
        description=f"{reported_user.name} 因违规已被封禁",
        color=discord.Color.red()
    )
    embed.add_field(name="举报人", value=reporter.mention, inline=False)
    embed.add_field(name="原因", value=report_payload['report_reason'], inline=False)
    
    await channel.send(
        f"{reporter.mention}",
        embed=embed
    )


async def execute_invalid(
    channel: discord.TextChannel,
    reporter: discord.User,
    reported_user: discord.Member,
):
    """执行驳回（误报）动作"""
    
    print(f"\n  [执行] 驳回举报...")
    
    embed = discord.Embed(
        title="❌ 举报已驳回",
        description=f"经审核，{reported_user.name} 的消息未发现违规",
        color=discord.Color.green()
    )
    
    await channel.send(
        f"{reporter.mention}",
        embed=embed
    )


async def escalate_to_gm(
    guild: discord.Guild,
    channel: discord.TextChannel,
    reporter: discord.User,
    reported_user: discord.Member,
    report_payload: dict,
):
    """升级到 GM（需要人工审核）"""
    
    print(f"\n  [执行] 升级到 GM...")
    
    # 获取 GM 角色
    gm_role = None
    for role in guild.roles:
        if role.name.lower() in ["gm", "管理员", "moderator"]:
            gm_role = role
            break
    
    if not gm_role:
        print(f"  [执行] 找不到 GM 角色")
        return
    
    # 发送通知
    embed = discord.Embed(
        title="⚠️ 需要 GM 审核",
        description="以下举报需要人工审核",
        color=discord.Color.orange()
    )
    embed.add_field(name="举报人", value=reporter.mention, inline=False)
    embed.add_field(name="被举报人", value=reported_user.mention, inline=False)
    embed.add_field(name="举报原因", value=report_payload['report_reason'], inline=False)
    embed.add_field(name="被举报消息", value=report_payload['reported_message_content'][:200], inline=False)
    
    await channel.send(
        f"{gm_role.mention}",
        embed=embed
    )


# ============================================================================
# 使用示例
# ============================================================================

"""
要在你的 Bot 中使用这个流程，按照以下方式集成：

1. 在 src/bot/client.py 中导入并注册事件处理器：

    from src.bot.events_impl import setup_event_handlers
    
    class LLMGuardBot(commands.Bot):
        def __init__(self):
            ...
        
        async def setup_hook(self):
            await setup_event_handlers(self)

2. 用户现在就可以这样举报：
   - 右键点击消息
   - 选择"回复"
   - 在回复中 @Bot 并输入举报原因
   - 例如：@Bot 这是杀猪盘

3. Bot 会自动：
   - 收集举报信息
   - 调用 LLM 分析
   - 执行对应的动作
"""

