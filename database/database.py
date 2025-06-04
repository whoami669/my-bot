import aiosqlite
import asyncio
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_path="bot_database.db"):
        self.db_path = db_path
        
    async def init_db(self):
        """Initialize the database with all required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Server settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    automod_enabled BOOLEAN DEFAULT FALSE,
                    xp_multiplier REAL DEFAULT 1.0,
                    settings_json TEXT DEFAULT '{}'
                )
            """)
            
            # User profiles and economy
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_economy (
                    guild_id INTEGER,
                    user_id INTEGER,
                    balance INTEGER DEFAULT 0,
                    bank INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    last_work TIMESTAMP,
                    last_crime TIMESTAMP,
                    last_rob TIMESTAMP,
                    daily_streak INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            
            # User XP and leveling
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_levels (
                    guild_id INTEGER,
                    user_id INTEGER,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            
            # Moderation warnings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reaction roles
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reaction_roles (
                    guild_id INTEGER,
                    message_id INTEGER,
                    emoji TEXT,
                    role_name TEXT,
                    PRIMARY KEY (guild_id, message_id, emoji)
                )
            """)
            
            # Tickets
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    guild_id INTEGER,
                    user_id INTEGER,
                    channel_id INTEGER PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    status TEXT DEFAULT 'open'
                )
            """)
            
            # Ticket messages for setup
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    guild_id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    category_id INTEGER
                )
            """)
            
            # Channel blacklist for XP
            await db.execute("""
                CREATE TABLE IF NOT EXISTS xp_blacklist (
                    guild_id INTEGER,
                    channel_id INTEGER,
                    PRIMARY KEY (guild_id, channel_id)
                )
            """)
            
            # Automod settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS automod_settings (
                    guild_id INTEGER PRIMARY KEY,
                    spam_protection BOOLEAN DEFAULT TRUE,
                    link_protection BOOLEAN DEFAULT FALSE,
                    word_filter BOOLEAN DEFAULT FALSE,
                    banned_words TEXT DEFAULT '[]'
                )
            """)
            
            await db.commit()

    # Server Management
    async def init_server(self, guild_id):
        """Initialize a server in the database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO server_settings (guild_id) VALUES (?)
            """, (guild_id,))
            await db.commit()

    async def get_prefix(self, guild_id):
        """Get the command prefix for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT prefix FROM server_settings WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else '!'

    async def set_prefix(self, guild_id, prefix):
        """Set the command prefix for a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO server_settings (guild_id, prefix) VALUES (?, ?)
            """, (guild_id, prefix))
            await db.commit()

    # Economy System
    async def get_balance(self, guild_id, user_id):
        """Get user's balance"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def add_balance(self, guild_id, user_id, amount):
        """Add to user's balance"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, balance) 
                VALUES (?, ?, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0) + ?)
            """, (guild_id, user_id, guild_id, user_id, amount))
            await db.commit()

    async def remove_balance(self, guild_id, user_id, amount):
        """Remove from user's balance"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, balance) 
                VALUES (?, ?, MAX(0, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0) - ?))
            """, (guild_id, user_id, guild_id, user_id, amount))
            await db.commit()

    async def get_last_daily(self, guild_id, user_id):
        """Get user's last daily claim"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT last_daily FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None

    async def get_daily_streak(self, guild_id, user_id):
        """Get user's daily streak"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT daily_streak FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def update_daily_streak(self, guild_id, user_id, streak):
        """Update user's daily streak"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, daily_streak, last_daily, balance) 
                VALUES (?, ?, ?, ?, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0))
            """, (guild_id, user_id, streak, datetime.utcnow().isoformat(), guild_id, user_id))
            await db.commit()

    async def get_last_work(self, guild_id, user_id):
        """Get user's last work time"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT last_work FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None

    async def update_last_work(self, guild_id, user_id):
        """Update user's last work time"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, last_work, balance) 
                VALUES (?, ?, ?, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0))
            """, (guild_id, user_id, datetime.utcnow().isoformat(), guild_id, user_id))
            await db.commit()

    async def get_last_crime(self, guild_id, user_id):
        """Get user's last crime time"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT last_crime FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None

    async def update_last_crime(self, guild_id, user_id):
        """Update user's last crime time"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, last_crime, balance) 
                VALUES (?, ?, ?, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0))
            """, (guild_id, user_id, datetime.utcnow().isoformat(), guild_id, user_id))
            await db.commit()

    async def get_last_rob(self, guild_id, user_id):
        """Get user's last rob time"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT last_rob FROM user_economy WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None

    async def update_last_rob(self, guild_id, user_id):
        """Update user's last rob time"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_economy (guild_id, user_id, last_rob, balance) 
                VALUES (?, ?, ?, COALESCE((SELECT balance FROM user_economy WHERE guild_id = ? AND user_id = ?), 0))
            """, (guild_id, user_id, datetime.utcnow().isoformat(), guild_id, user_id))
            await db.commit()

    async def get_top_balances(self, guild_id, limit=10):
        """Get top balances in the server"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, balance FROM user_economy 
                WHERE guild_id = ? ORDER BY balance DESC LIMIT ?
            """, (guild_id, limit)) as cursor:
                return await cursor.fetchall()

    # Leveling System
    async def get_user_xp(self, guild_id, user_id):
        """Get user's XP"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT xp FROM user_levels WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def get_level(self, guild_id, user_id):
        """Get user's level"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT level FROM user_levels WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def add_xp(self, guild_id, user_id, xp_amount):
        """Add XP to user and update level"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get current XP
            current_xp = await self.get_user_xp(guild_id, user_id)
            new_xp = current_xp + xp_amount
            
            # Calculate new level
            new_level = self.calculate_level(new_xp)
            
            await db.execute("""
                INSERT OR REPLACE INTO user_levels (guild_id, user_id, xp, level, messages) 
                VALUES (?, ?, ?, ?, COALESCE((SELECT messages FROM user_levels WHERE guild_id = ? AND user_id = ?), 0) + 1)
            """, (guild_id, user_id, new_xp, new_level, guild_id, user_id))
            await db.commit()

    async def set_user_xp(self, guild_id, user_id, xp):
        """Set user's XP"""
        level = self.calculate_level(xp)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO user_levels (guild_id, user_id, xp, level, messages) 
                VALUES (?, ?, ?, ?, COALESCE((SELECT messages FROM user_levels WHERE guild_id = ? AND user_id = ?), 0))
            """, (guild_id, user_id, xp, level, guild_id, user_id))
            await db.commit()

    async def get_user_stats(self, guild_id, user_id):
        """Get all user stats"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT xp, level, messages FROM user_levels WHERE guild_id = ? AND user_id = ?
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return {'xp': result[0], 'level': result[1], 'messages': result[2]}
                return {'xp': 0, 'level': 0, 'messages': 0}

    async def get_user_rank(self, guild_id, user_id):
        """Get user's rank in the server"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT COUNT(*) + 1 FROM user_levels 
                WHERE guild_id = ? AND xp > (SELECT COALESCE(xp, 0) FROM user_levels WHERE guild_id = ? AND user_id = ?)
            """, (guild_id, guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 1

    async def get_top_users(self, guild_id, limit=10):
        """Get top users by XP"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, xp, level FROM user_levels 
                WHERE guild_id = ? ORDER BY xp DESC LIMIT ?
            """, (guild_id, limit)) as cursor:
                results = await cursor.fetchall()
                return [{'user_id': r[0], 'xp': r[1], 'level': r[2]} for r in results]

    async def reset_all_levels(self, guild_id):
        """Reset all user levels in a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM user_levels WHERE guild_id = ?
            """, (guild_id,))
            await db.commit()

    async def set_xp_multiplier(self, guild_id, multiplier):
        """Set XP multiplier for the server"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO server_settings (guild_id, xp_multiplier) VALUES (?, ?)
            """, (guild_id, multiplier))
            await db.commit()

    async def is_channel_blacklisted(self, guild_id, channel_id):
        """Check if channel is blacklisted from XP"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT 1 FROM xp_blacklist WHERE guild_id = ? AND channel_id = ?
            """, (guild_id, channel_id)) as cursor:
                return await cursor.fetchone() is not None

    async def add_channel_blacklist(self, guild_id, channel_id):
        """Add channel to XP blacklist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO xp_blacklist (guild_id, channel_id) VALUES (?, ?)
            """, (guild_id, channel_id))
            await db.commit()

    async def remove_channel_blacklist(self, guild_id, channel_id):
        """Remove channel from XP blacklist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM xp_blacklist WHERE guild_id = ? AND channel_id = ?
            """, (guild_id, channel_id))
            await db.commit()

    @staticmethod
    def calculate_level(xp):
        """Calculate level from XP"""
        if xp <= 0:
            return 0
        # Level formula: level = floor(sqrt(xp / 50))
        import math
        return int(math.sqrt(xp / 50))

    # Moderation System
    async def add_warning(self, guild_id, user_id, moderator_id, reason):
        """Add a warning to a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)
            """, (guild_id, user_id, moderator_id, reason))
            await db.commit()

    async def get_warnings(self, guild_id, user_id):
        """Get all warnings for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT moderator_id, reason, timestamp FROM warnings 
                WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC
            """, (guild_id, user_id)) as cursor:
                results = await cursor.fetchall()
                return [{'moderator_id': r[0], 'reason': r[1], 'timestamp': datetime.fromisoformat(r[2])} for r in results]

    # Reaction Roles
    async def add_reaction_role_message(self, guild_id, message_id, role_emojis):
        """Add reaction role message"""
        async with aiosqlite.connect(self.db_path) as db:
            for emoji, role_name in role_emojis.items():
                await db.execute("""
                    INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_name) VALUES (?, ?, ?, ?)
                """, (guild_id, message_id, emoji, role_name))
            await db.commit()

    async def get_reaction_roles(self, guild_id, message_id):
        """Get reaction roles for a message"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT emoji, role_name FROM reaction_roles WHERE guild_id = ? AND message_id = ?
            """, (guild_id, message_id)) as cursor:
                results = await cursor.fetchall()
                return {r[0]: r[1] for r in results}

    # Ticket System
    async def set_ticket_message(self, guild_id, message_id, category_id):
        """Set ticket creation message"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO ticket_messages (guild_id, message_id, category_id) VALUES (?, ?, ?)
            """, (guild_id, message_id, category_id))
            await db.commit()

    async def get_ticket_message(self, guild_id, message_id):
        """Get ticket message data"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT category_id FROM ticket_messages WHERE guild_id = ? AND message_id = ?
            """, (guild_id, message_id)) as cursor:
                result = await cursor.fetchone()
                return {'category_id': result[0]} if result else None

    async def create_ticket(self, guild_id, user_id, channel_id):
        """Create a new ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO tickets (guild_id, user_id, channel_id) VALUES (?, ?, ?)
            """, (guild_id, user_id, channel_id))
            await db.commit()

    async def get_user_ticket(self, guild_id, user_id):
        """Get user's open ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT channel_id, created_at FROM tickets 
                WHERE guild_id = ? AND user_id = ? AND status = 'open'
            """, (guild_id, user_id)) as cursor:
                result = await cursor.fetchone()
                return {'channel_id': result[0], 'created_at': result[1]} if result else None

    async def get_ticket_by_channel(self, guild_id, channel_id):
        """Get ticket by channel ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, created_at FROM tickets 
                WHERE guild_id = ? AND channel_id = ? AND status = 'open'
            """, (guild_id, channel_id)) as cursor:
                result = await cursor.fetchone()
                return {'user_id': result[0], 'created_at': result[1]} if result else None

    async def close_ticket(self, guild_id, channel_id):
        """Close a ticket"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE tickets SET status = 'closed', closed_at = ? 
                WHERE guild_id = ? AND channel_id = ?
            """, (datetime.utcnow().isoformat(), guild_id, channel_id))
            await db.commit()

    async def get_all_tickets(self, guild_id):
        """Get all open tickets"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, channel_id, created_at FROM tickets 
                WHERE guild_id = ? AND status = 'open' ORDER BY created_at DESC
            """, (guild_id,)) as cursor:
                results = await cursor.fetchall()
                return [{'user_id': r[0], 'channel_id': r[1], 'created_at': r[2]} for r in results]

    async def get_ticket_stats(self, guild_id):
        """Get ticket statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Open tickets
            async with db.execute("""
                SELECT COUNT(*) FROM tickets WHERE guild_id = ? AND status = 'open'
            """, (guild_id,)) as cursor:
                open_count = (await cursor.fetchone())[0]
            
            # Total tickets
            async with db.execute("""
                SELECT COUNT(*) FROM tickets WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                total_count = (await cursor.fetchone())[0]
            
            # Closed today
            today = datetime.utcnow().date().isoformat()
            async with db.execute("""
                SELECT COUNT(*) FROM tickets 
                WHERE guild_id = ? AND status = 'closed' AND DATE(closed_at) = ?
            """, (guild_id, today)) as cursor:
                closed_today = (await cursor.fetchone())[0]
            
            return {
                'open': open_count,
                'total': total_count,
                'closed_today': closed_today
            }

    # Server Settings
    async def update_server_settings(self, guild_id, settings):
        """Update server settings"""
        async with aiosqlite.connect(self.db_path) as db:
            settings_json = json.dumps(settings)
            await db.execute("""
                INSERT OR REPLACE INTO server_settings (guild_id, settings_json) VALUES (?, ?)
            """, (guild_id, settings_json))
            await db.commit()

    async def get_server_settings(self, guild_id):
        """Get server settings"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT settings_json FROM server_settings WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                result = await cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                return {}

    # Backup System
    async def backup_server_data(self, guild_id):
        """Backup all data for a server"""
        backup_data = {
            'guild_id': guild_id,
            'timestamp': datetime.utcnow().isoformat(),
            'economy': [],
            'levels': [],
            'warnings': [],
            'tickets': []
        }
        
        async with aiosqlite.connect(self.db_path) as db:
            # Economy data
            async with db.execute("""
                SELECT * FROM user_economy WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                backup_data['economy'] = await cursor.fetchall()
            
            # Level data
            async with db.execute("""
                SELECT * FROM user_levels WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                backup_data['levels'] = await cursor.fetchall()
            
            # Warning data
            async with db.execute("""
                SELECT * FROM warnings WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                backup_data['warnings'] = await cursor.fetchall()
            
            # Ticket data
            async with db.execute("""
                SELECT * FROM tickets WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                backup_data['tickets'] = await cursor.fetchall()
        
        # Save backup to file
        import json
        backup_filename = f"backup_{guild_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        return backup_filename
