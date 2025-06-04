import discord
from datetime import datetime

def create_embed(title=None, description=None, color=None, timestamp=None):
    """Create a basic embed with consistent styling"""
    if color is None:
        color = 0x7289DA  # Discord Blurple
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=timestamp or datetime.utcnow()
    )
    
    return embed

def success_embed(title, description=None):
    """Create a success embed (green)"""
    return create_embed(
        title=f"✅ {title}",
        description=description,
        color=0x00FF00
    )

def error_embed(title, description=None):
    """Create an error embed (red)"""
    return create_embed(
        title=f"❌ {title}",
        description=description,
        color=0xFF0000
    )

def warning_embed(title, description=None):
    """Create a warning embed (yellow)"""
    return create_embed(
        title=f"⚠️ {title}",
        description=description,
        color=0xFFFF00
    )

def info_embed(title, description=None):
    """Create an info embed (blue)"""
    return create_embed(
        title=f"ℹ️ {title}",
        description=description,
        color=0x0099FF
    )

def loading_embed(title="Loading...", description=None):
    """Create a loading embed"""
    return create_embed(
        title=f"⏳ {title}",
        description=description,
        color=0xFFA500
    )

def create_user_embed(user, title=None, description=None, color=None):
    """Create an embed with user information"""
    if not color:
        color = user.color if hasattr(user, 'color') and user.color != discord.Color.default() else 0x7289DA
    
    embed = create_embed(title=title, description=description, color=color)
    
    # Set user avatar as thumbnail
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    embed.set_thumbnail(url=avatar_url)
    
    return embed

def create_server_embed(guild, title=None, description=None, color=0x7289DA):
    """Create an embed with server information"""
    embed = create_embed(title=title, description=description, color=color)
    
    # Set server icon as thumbnail
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    return embed

def paginate_embed(items, title, per_page=10, color=0x7289DA):
    """Create paginated embeds for long lists"""
    pages = []
    
    for i in range(0, len(items), per_page):
        chunk = items[i:i + per_page]
        embed = create_embed(
            title=f"{title} (Page {i//per_page + 1}/{(len(items)-1)//per_page + 1})",
            color=color
        )
        
        for item in chunk:
            if isinstance(item, dict):
                embed.add_field(
                    name=item.get('name', 'Unknown'),
                    value=item.get('value', 'No value'),
                    inline=item.get('inline', True)
                )
            else:
                embed.add_field(
                    name=f"Item {chunk.index(item) + 1}",
                    value=str(item),
                    inline=True
                )
        
        pages.append(embed)
    
    return pages

def create_help_embed(command=None, commands=None, prefix="!"):
    """Create a help embed for commands"""
    if command:
        # Single command help
        embed = create_embed(
            title=f"Help: {command.name}",
            description=command.help or "No description available",
            color=0x7289DA
        )
        
        if hasattr(command, 'usage') and command.usage:
            embed.add_field(
                name="Usage",
                value=f"`{prefix}{command.name} {command.usage}`",
                inline=False
            )
        
        if hasattr(command, 'aliases') and command.aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False
            )
        
        if hasattr(command, 'cooldown') and command.cooldown:
            embed.add_field(
                name="Cooldown",
                value=f"{command.cooldown.per} seconds",
                inline=True
            )
    
    else:
        # General help
        embed = create_embed(
            title="🤖 Bot Help",
            description="Here are all available commands",
            color=0x7289DA
        )
        
        if commands:
            # Group commands by cog
            cog_commands = {}
            for cmd in commands:
                cog_name = cmd.cog_name or "General"
                if cog_name not in cog_commands:
                    cog_commands[cog_name] = []
                cog_commands[cog_name].append(cmd.name)
            
            for cog_name, cmd_names in cog_commands.items():
                embed.add_field(
                    name=f"📂 {cog_name}",
                    value=", ".join(f"`{cmd}`" for cmd in cmd_names[:8]) + (f"\n... and {len(cmd_names) - 8} more" if len(cmd_names) > 8 else ""),
                    inline=False
                )
        
        embed.add_field(
            name="💡 Need more help?",
            value=f"Use `{prefix}help <command>` for detailed command information",
            inline=False
        )
    
    return embed

def create_moderation_embed(action, target, moderator, reason=None, duration=None):
    """Create a moderation action embed"""
    action_colors = {
        'ban': 0xFF0000,
        'kick': 0xFF4500,
        'mute': 0xFFA500,
        'warn': 0xFFFF00,
        'unmute': 0x00FF00,
        'unban': 0x00FF00
    }
    
    action_emojis = {
        'ban': '🔨',
        'kick': '👢',
        'mute': '🔇',
        'warn': '⚠️',
        'unmute': '🔊',
        'unban': '✅'
    }
    
    color = action_colors.get(action.lower(), 0x7289DA)
    emoji = action_emojis.get(action.lower(), '📋')
    
    embed = create_embed(
        title=f"{emoji} {action.title()}",
        description=f"Action taken against {target.mention if hasattr(target, 'mention') else target}",
        color=color
    )
    
    embed.add_field(name="Target", value=str(target), inline=True)
    embed.add_field(name="Moderator", value=str(moderator), inline=True)
    
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    
    if duration:
        embed.add_field(name="Duration", value=duration, inline=True)
    
    embed.set_footer(text=f"User ID: {target.id if hasattr(target, 'id') else 'Unknown'}")
    
    return embed

def create_economy_embed(user, title, amount=None, balance=None, color=0xFFD700):
    """Create an economy-related embed"""
    embed = create_user_embed(user, title=title, color=color)
    
    if amount is not None:
        embed.add_field(name="Amount", value=f"{amount:,} coins", inline=True)
    
    if balance is not None:
        embed.add_field(name="Balance", value=f"{balance:,} coins", inline=True)
    
    return embed

def create_level_embed(user, level, xp, rank=None):
    """Create a leveling embed"""
    embed = create_user_embed(
        user,
        title=f"📊 {user.display_name}'s Level",
        color=0x7289DA
    )
    
    embed.add_field(name="Level", value=str(level), inline=True)
    embed.add_field(name="XP", value=f"{xp:,}", inline=True)
    
    if rank:
        embed.add_field(name="Rank", value=f"#{rank}", inline=True)
    
    return embed

def create_music_embed(title, description=None, thumbnail=None, color=0x1DB954):
    """Create a music-related embed"""
    embed = create_embed(title=title, description=description, color=color)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    return embed

def create_ticket_embed(action, user, ticket_id=None, reason=None):
    """Create a ticket-related embed"""
    action_colors = {
        'created': 0x00FF00,
        'closed': 0xFF0000,
        'claimed': 0xFFD700
    }
    
    action_emojis = {
        'created': '🎫',
        'closed': '🔒',
        'claimed': '👷'
    }
    
    color = action_colors.get(action.lower(), 0x7289DA)
    emoji = action_emojis.get(action.lower(), '🎫')
    
    embed = create_embed(
        title=f"{emoji} Ticket {action.title()}",
        color=color
    )
    
    embed.add_field(name="User", value=user.mention, inline=True)
    
    if ticket_id:
        embed.add_field(name="Ticket ID", value=str(ticket_id), inline=True)
    
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    return embed

def create_poll_embed(question, options=None, author=None):
    """Create a poll embed"""
    embed = create_embed(
        title="📊 Poll",
        description=question,
        color=0x7289DA
    )
    
    if options:
        if isinstance(options, dict):
            # Reaction-based poll
            options_text = ""
            for emoji, option in options.items():
                options_text += f"{emoji} {option}\n"
            embed.add_field(name="Options", value=options_text, inline=False)
        else:
            # Simple yes/no poll
            embed.add_field(name="Options", value="👍 Yes\n👎 No", inline=False)
    
    if author:
        embed.set_footer(text=f"Poll by {author.display_name}", icon_url=author.avatar.url if author.avatar else author.default_avatar.url)
    
    return embed

def create_leaderboard_embed(title, entries, medal_emojis=None):
    """Create a leaderboard embed"""
    if not medal_emojis:
        medal_emojis = ["🥇", "🥈", "🥉"]
    
    embed = create_embed(
        title=f"🏆 {title}",
        color=0xFFD700
    )
    
    for i, entry in enumerate(entries[:10], 1):  # Top 10
        if i <= len(medal_emojis):
            position = medal_emojis[i-1]
        else:
            position = f"{i}."
        
        if isinstance(entry, dict):
            name = entry.get('name', f'Entry {i}')
            value = entry.get('value', 'No value')
        elif isinstance(entry, tuple):
            name, value = entry
        else:
            name = f"Entry {i}"
            value = str(entry)
        
        embed.add_field(
            name=f"{position} {name}",
            value=str(value),
            inline=False
        )
    
    return embed

def create_status_embed(bot):
    """Create a bot status embed"""
    embed = create_embed(
        title="🤖 Bot Status",
        color=0x00FF00
    )
    
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Users", value=str(sum(guild.member_count for guild in bot.guilds)), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    if hasattr(bot, 'start_time'):
        uptime = datetime.utcnow() - bot.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        embed.add_field(
            name="Uptime",
            value=f"{days}d {hours}h {minutes}m",
            inline=True
        )
    
    return embed
