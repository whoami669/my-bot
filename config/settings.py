import discord

# Default bot settings
DEFAULT_SETTINGS = {
    'prefix': '!',
    'automod_enabled': False,
    'welcome_enabled': True,
    'leveling_enabled': True,
    'economy_enabled': True,
    'music_enabled': True,
    'tickets_enabled': True
}

# Comprehensive server channel structure
CATEGORIES = {
    "📋 Server Info": [
        {"name": "welcome", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "rules", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "announcements", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "server-updates", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "reaction-roles", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}}
    ],
    
    "💬 General Chat": [
        {"name": "general-chat", "type": "text"},
        {"name": "introductions", "type": "text"},
        {"name": "off-topic", "type": "text"},
        {"name": "bot-commands", "type": "text"},
        {"name": "counting", "type": "text"},
        {"name": "word-association", "type": "text"}
    ],
    
    "🎮 Gaming": [
        {"name": "gaming-lounge", "type": "text"},
        {"name": "find-a-squad", "type": "text"},
        {"name": "game-clips", "type": "text"},
        {"name": "screenshots", "type": "text"},
        {"name": "game-reviews", "type": "text"},
        {"name": "esports", "type": "text"},
        {"name": "minecraft", "type": "text"},
        {"name": "valorant", "type": "text"},
        {"name": "league-of-legends", "type": "text"},
        {"name": "fortnite", "type": "text"}
    ],
    
    "🎵 Music & Media": [
        {"name": "music-chat", "type": "text"},
        {"name": "music-commands", "type": "text"},
        {"name": "movie-tv", "type": "text"},
        {"name": "anime-manga", "type": "text"},
        {"name": "art-showcase", "type": "text"},
        {"name": "photography", "type": "text"}
    ],
    
    "💰 Economy": [
        {"name": "economy-commands", "type": "text"},
        {"name": "trading", "type": "text"},
        {"name": "gambling", "type": "text"},
        {"name": "shop", "type": "text"}
    ],
    
    "🎭 Fun & Games": [
        {"name": "memes", "type": "text"},
        {"name": "games", "type": "text"},
        {"name": "trivia", "type": "text"},
        {"name": "polls", "type": "text"},
        {"name": "suggestions", "type": "text"},
        {"name": "confessions", "type": "text"}
    ],
    
    "📚 Study & Work": [
        {"name": "study-hall", "type": "text"},
        {"name": "homework-help", "type": "text"},
        {"name": "programming", "type": "text"},
        {"name": "resources", "type": "text"},
        {"name": "career-advice", "type": "text"}
    ],
    
    "🏃 Fitness & Health": [
        {"name": "fitness", "type": "text"},
        {"name": "nutrition", "type": "text"},
        {"name": "mental-health", "type": "text"},
        {"name": "workout-buddies", "type": "text"}
    ],
    
    "🎫 Support": [
        {"name": "create-ticket", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "faq", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "report-bugs", "type": "text"}
    ],
    
    "🔊 Voice Channels": [
        {"name": "General Lounge", "type": "voice"},
        {"name": "Music Listening", "type": "voice"},
        {"name": "Gaming Room 1", "type": "voice"},
        {"name": "Gaming Room 2", "type": "voice"},
        {"name": "Gaming Room 3", "type": "voice"},
        {"name": "Study Group", "type": "voice"},
        {"name": "Chill Zone", "type": "voice"},
        {"name": "Private Room 1", "type": "voice", "overwrites": {"@everyone": {"connect": False}}},
        {"name": "Private Room 2", "type": "voice", "overwrites": {"@everyone": {"connect": False}}},
        {"name": "AFK", "type": "voice"}
    ],
    
    "🎤 Events": [
        {"name": "event-announcements", "type": "text", "overwrites": {"@everyone": {"send_messages": False}}},
        {"name": "event-planning", "type": "text"},
        {"name": "event-chat", "type": "text"},
        {"name": "Event Stage", "type": "voice"}
    ],
    
    "⚙️ Staff Only": [
        {"name": "staff-chat", "type": "text", "overwrites": {
            "@everyone": {"read_messages": False},
            "Admin": {"read_messages": True, "send_messages": True},
            "Moderator": {"read_messages": True, "send_messages": True},
            "Helper": {"read_messages": True, "send_messages": True}
        }},
        {"name": "mod-logs", "type": "text", "overwrites": {
            "@everyone": {"read_messages": False},
            "Admin": {"read_messages": True, "send_messages": True},
            "Moderator": {"read_messages": True, "send_messages": True}
        }},
        {"name": "member-logs", "type": "text", "overwrites": {
            "@everyone": {"read_messages": False},
            "Admin": {"read_messages": True, "send_messages": True},
            "Moderator": {"read_messages": True, "send_messages": True}
        }},
        {"name": "ticket-logs", "type": "text", "overwrites": {
            "@everyone": {"read_messages": False},
            "Admin": {"read_messages": True, "send_messages": True},
            "Moderator": {"read_messages": True, "send_messages": True}
        }},
        {"name": "Staff Meeting", "type": "voice", "overwrites": {
            "@everyone": {"connect": False},
            "Admin": {"connect": True, "speak": True},
            "Moderator": {"connect": True, "speak": True}
        }}
    ]
}

# Bot permissions needed for full functionality
BOT_PERMISSIONS = discord.Permissions(
    read_messages=True,
    send_messages=True,
    manage_messages=True,
    embed_links=True,
    attach_files=True,
    read_message_history=True,
    add_reactions=True,
    use_external_emojis=True,
    manage_channels=True,
    manage_roles=True,
    kick_members=True,
    ban_members=True,
    manage_guild=True,
    connect=True,
    speak=True,
    mute_members=True,
    deafen_members=True,
    move_members=True,
    use_voice_activation=True,
    manage_nicknames=True,
    manage_webhooks=True,
    manage_emojis=True,
    view_audit_log=True
)

# Automod settings
AUTOMOD_SETTINGS = {
    'spam_detection': {
        'enabled': True,
        'max_messages': 5,
        'time_window': 10,  # seconds
        'punishment': 'mute',
        'duration': 300  # 5 minutes
    },
    'link_detection': {
        'enabled': False,
        'whitelist': ['discord.gg', 'youtube.com', 'youtu.be', 'twitch.tv'],
        'punishment': 'delete'
    },
    'word_filter': {
        'enabled': False,
        'banned_words': [],
        'punishment': 'delete'
    },
    'caps_detection': {
        'enabled': True,
        'threshold': 70,  # percentage
        'min_length': 10,
        'punishment': 'delete'
    },
    'mention_spam': {
        'enabled': True,
        'max_mentions': 5,
        'punishment': 'delete'
    }
}

# Economy settings
ECONOMY_SETTINGS = {
    'daily_reward': {
        'base_amount': 100,
        'streak_bonus': 10,
        'max_streak_bonus': 500
    },
    'work_rewards': {
        'cooldown': 3600,  # 1 hour
        'min_reward': 50,
        'max_reward': 200
    },
    'crime_settings': {
        'cooldown': 7200,  # 2 hours
        'success_rate': 0.6,
        'min_reward': 200,
        'max_reward': 500,
        'min_fine': 100,
        'max_fine': 300
    },
    'gambling': {
        'win_rate': 0.45,
        'max_bet': 10000
    },
    'rob_settings': {
        'cooldown': 14400,  # 4 hours
        'success_rate': 0.35,
        'max_steal_percentage': 0.5
    }
}

# Leveling settings
LEVELING_SETTINGS = {
    'xp_per_message': {
        'min': 15,
        'max': 25
    },
    'level_formula': {
        'base': 50,
        'multiplier': 1
    },
    'rewards': {
        'coins_per_level': 100,
        'role_rewards': {
            5: 'Level 5',
            10: 'Level 10',
            25: 'Level 25',
            50: 'Level 50',
            75: 'Level 75',
            100: 'Level 100'
        }
    },
    'blacklisted_channels': []
}

# Music settings
MUSIC_SETTINGS = {
    'max_queue_size': 100,
    'max_song_duration': 3600,  # 1 hour
    'volume_default': 50,
    'volume_max': 100,
    'auto_disconnect_timeout': 300,  # 5 minutes
    'search_results_limit': 10
}

# Moderation settings
MODERATION_SETTINGS = {
    'log_actions': True,
    'dm_on_punishment': True,
    'auto_role_assignment': True,
    'default_mute_role': 'Muted',
    'warn_thresholds': {
        3: 'mute_1h',
        5: 'mute_24h',
        7: 'kick',
        10: 'ban'
    }
}

# Ticket settings
TICKET_SETTINGS = {
    'support_roles': ['Admin', 'Moderator', 'Helper', 'Staff'],
    'max_tickets_per_user': 1,
    'auto_close_inactive': 7,  # days
    'transcript_channel': 'ticket-logs',
    'ping_support_on_create': True
}

# Fun command settings
FUN_SETTINGS = {
    'meme_sources': ['memes', 'dankmemes', 'wholesomememes', 'ProgrammerHumor'],
    'fact_api_enabled': True,
    'quote_api_enabled': True,
    'weather_api_enabled': False
}

# Rate limiting
RATE_LIMITS = {
    'commands_per_minute': 30,
    'music_commands_per_minute': 10,
    'economy_commands_per_hour': 20,
    'moderation_commands_per_minute': 5
}

# Status messages for bot presence
STATUS_MESSAGES = [
    {"type": "watching", "name": "{guilds} servers"},
    {"type": "listening", "name": "your commands"},
    {"type": "playing", "name": "with Discord.py"},
    {"type": "competing", "name": "server management"},
    {"type": "watching", "name": "{members} members"},
    {"type": "playing", "name": "music for everyone"},
    {"type": "listening", "name": "to feedback"},
    {"type": "watching", "name": "for new features"}
]

# Logging configuration
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_to_file': True,
    'log_file': 'bot.log',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# API Keys and external services
EXTERNAL_APIS = {
    'weather_api_key': None,
    'news_api_key': None,
    'translate_api_key': None,
    'image_api_key': None
}

# Feature flags
FEATURE_FLAGS = {
    'beta_features': False,
    'experimental_commands': False,
    'premium_features': False,
    'analytics': True,
    'error_reporting': True
}

# Database settings
DATABASE_CONFIG = {
    'type': 'sqlite',
    'path': 'bot_database.db',
    'backup_interval': 86400,  # 24 hours
    'cleanup_interval': 604800,  # 7 days
    'retain_logs': 2592000  # 30 days
}

# Security settings
SECURITY_CONFIG = {
    'owner_only_commands': ['eval', 'exec', 'shutdown', 'restart'],
    'admin_only_commands': ['ban', 'kick', 'purge', 'lockdown'],
    'rate_limit_punishment': 'temp_ban',
    'suspicious_activity_threshold': 10,
    'auto_ban_spam_bots': True
}
