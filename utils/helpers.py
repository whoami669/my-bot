import discord
from datetime import datetime, timezone
import re

def format_time(dt):
    """Format datetime to a readable string"""
    if dt is None:
        return "Unknown"
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    # If less than a minute ago
    if diff.total_seconds() < 60:
        return "Just now"
    
    # If less than an hour ago
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    
    # If less than a day ago
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    # If less than a week ago
    elif diff.total_seconds() < 604800:
        days = int(diff.total_seconds() // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    
    # Otherwise, return formatted date
    else:
        return dt.strftime("%B %d, %Y at %I:%M %p UTC")

def format_duration(seconds):
    """Format seconds to a readable duration string"""
    if seconds < 60:
        return f"{int(seconds)} second{'s' if seconds != 1 else ''}"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    if hours < 24:
        return f"{int(hours)} hour{'s' if hours != 1 else ''}"
    
    days = hours // 24
    return f"{int(days)} day{'s' if days != 1 else ''}"

def parse_time(time_str):
    """Parse time string like '1h', '30m', '2d' to seconds"""
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    match = re.match(r'^(\d+)([smhdw])$', time_str.lower())
    if not match:
        return None
    
    amount, unit = match.groups()
    return int(amount) * time_units[unit]

async def get_prefix(bot, message):
    """Get the command prefix for a guild"""
    if not message.guild:
        return '!'
    
    # Get prefix from database
    prefix = await bot.db.get_prefix(message.guild.id)
    return prefix

def clean_text(text, max_length=2000):
    """Clean and truncate text for Discord"""
    if not text:
        return "No content"
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length - 3] + "..."
    
    return text

def escape_markdown(text):
    """Escape Discord markdown characters"""
    markdown_chars = ['*', '_', '`', '~', '|', '\\']
    for char in markdown_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_number(number):
    """Format large numbers with commas"""
    return f"{number:,}"

def truncate_string(text, max_length=100, suffix="..."):
    """Truncate a string to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def get_member_color(member):
    """Get a member's role color or default"""
    if member.color != discord.Color.default():
        return member.color
    return discord.Color.blurple()

def permission_check(required_permission):
    """Decorator to check if user has required permission"""
    async def predicate(ctx):
        if ctx.author.guild_permissions.__getattribute__(required_permission):
            return True
        raise discord.ext.commands.MissingPermissions([required_permission])
    return discord.ext.commands.check(predicate)

def is_staff():
    """Check if user is staff (has moderation permissions or staff role)"""
    async def predicate(ctx):
        if ctx.author.guild_permissions.manage_messages:
            return True
        
        staff_roles = ['admin', 'administrator', 'mod', 'moderator', 'staff', 'helper']
        user_roles = [role.name.lower() for role in ctx.author.roles]
        
        return any(staff_role in user_roles for staff_role in staff_roles)
    
    return discord.ext.commands.check(predicate)

def format_permissions(permissions):
    """Format permission names to be more readable"""
    permission_names = {
        'create_instant_invite': 'Create Instant Invite',
        'kick_members': 'Kick Members',
        'ban_members': 'Ban Members',
        'administrator': 'Administrator',
        'manage_channels': 'Manage Channels',
        'manage_guild': 'Manage Server',
        'add_reactions': 'Add Reactions',
        'view_audit_log': 'View Audit Log',
        'priority_speaker': 'Priority Speaker',
        'stream': 'Video',
        'read_messages': 'Read Text Channels & See Voice Channels',
        'send_messages': 'Send Messages',
        'send_tts_messages': 'Send TTS Messages',
        'manage_messages': 'Manage Messages',
        'embed_links': 'Embed Links',
        'attach_files': 'Attach Files',
        'read_message_history': 'Read Message History',
        'mention_everyone': 'Mention Everyone',
        'external_emojis': 'Use External Emojis',
        'view_guild_insights': 'View Server Insights',
        'connect': 'Connect',
        'speak': 'Speak',
        'mute_members': 'Mute Members',
        'deafen_members': 'Deafen Members',
        'move_members': 'Move Members',
        'use_voice_activation': 'Use Voice Activity',
        'change_nickname': 'Change Nickname',
        'manage_nicknames': 'Manage Nicknames',
        'manage_roles': 'Manage Roles',
        'manage_webhooks': 'Manage Webhooks',
        'manage_emojis': 'Manage Emojis',
        'use_slash_commands': 'Use Slash Commands',
        'request_to_speak': 'Request to Speak',
        'manage_threads': 'Manage Threads',
        'create_public_threads': 'Create Public Threads',
        'create_private_threads': 'Create Private Threads',
        'send_messages_in_threads': 'Send Messages in Threads',
        'use_external_stickers': 'Use External Stickers',
        'moderate_members': 'Timeout Members'
    }
    
    formatted = []
    for permission, value in permissions:
        if value and permission in permission_names:
            formatted.append(permission_names[permission])
    
    return formatted

def get_status_emoji(status):
    """Get emoji for user status"""
    status_emojis = {
        discord.Status.online: "🟢",
        discord.Status.idle: "🟡",
        discord.Status.dnd: "🔴",
        discord.Status.offline: "⚫"
    }
    return status_emojis.get(status, "⚫")

def progress_bar(current, total, length=20, fill="█", empty="░"):
    """Create a progress bar"""
    if total == 0:
        percentage = 0
    else:
        percentage = min(100, (current / total) * 100)
    
    filled_length = int(length * percentage / 100)
    bar = fill * filled_length + empty * (length - filled_length)
    
    return f"{bar} {percentage:.1f}%"

def ordinal(n):
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def chunk_list(lst, chunk_size):
    """Split a list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def validate_hex_color(color_string):
    """Validate and convert hex color string"""
    if not color_string.startswith('#'):
        color_string = '#' + color_string
    
    if len(color_string) != 7:
        return None
    
    try:
        int(color_string[1:], 16)
        return color_string
    except ValueError:
        return None

def safe_divide(a, b):
    """Safely divide two numbers, return 0 if division by zero"""
    try:
        return a / b
    except ZeroDivisionError:
        return 0

def mentions_to_text(content, guild):
    """Convert mentions in content to readable text"""
    # Replace user mentions
    def replace_user_mention(match):
        user_id = int(match.group(1))
        member = guild.get_member(user_id)
        return f"@{member.display_name}" if member else f"@Unknown User"
    
    # Replace role mentions
    def replace_role_mention(match):
        role_id = int(match.group(1))
        role = guild.get_role(role_id)
        return f"@{role.name}" if role else f"@Unknown Role"
    
    # Replace channel mentions
    def replace_channel_mention(match):
        channel_id = int(match.group(1))
        channel = guild.get_channel(channel_id)
        return f"#{channel.name}" if channel else f"#Unknown Channel"
    
    content = re.sub(r'<@!?(\d+)>', replace_user_mention, content)
    content = re.sub(r'<@&(\d+)>', replace_role_mention, content)
    content = re.sub(r'<#(\d+)>', replace_channel_mention, content)
    
    return content

def is_image_url(url):
    """Check if URL is an image"""
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
    return any(url.lower().endswith(ext) for ext in image_extensions)

def get_webhook_avatar(member):
    """Get appropriate avatar URL for webhook"""
    if member.avatar:
        return member.avatar.url
    return member.default_avatar.url
