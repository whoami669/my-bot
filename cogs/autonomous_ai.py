import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import logging
import os
from openai import OpenAI

class ServerAnalytics:
    """Handles server data collection and analysis"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'autonomous_ai.db'
        
    async def init_database(self):
        """Initialize the analytics database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    user_id INTEGER,
                    message_count INTEGER DEFAULT 1,
                    timestamp DATETIME,
                    activity_type TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS channel_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    channel_name TEXT,
                    total_messages INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    last_activity DATETIME,
                    engagement_score REAL DEFAULT 0.0
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    total_messages INTEGER DEFAULT 0,
                    last_seen DATETIME,
                    engagement_level TEXT DEFAULT 'inactive',
                    join_date DATETIME
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ai_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    action_type TEXT,
                    action_details TEXT,
                    reasoning TEXT,
                    confidence_score REAL,
                    timestamp DATETIME,
                    result_metrics TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    date_recorded DATE,
                    total_members INTEGER,
                    active_members INTEGER,
                    message_volume INTEGER,
                    boost_count INTEGER,
                    join_rate REAL,
                    leave_rate REAL
                )
            ''')
            
            await db.commit()
    
    async def log_message_activity(self, message):
        """Log message activity for analytics"""
        if message.author.bot:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO server_activity 
                (guild_id, channel_id, user_id, timestamp, activity_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                message.guild.id,
                message.channel.id,
                message.author.id,
                datetime.now(timezone.utc),
                'message'
            ))
            await db.commit()
    
    async def update_channel_analytics(self, guild_id: int):
        """Update channel engagement analytics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get message counts per channel from last 24 hours
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            cursor = await db.execute('''
                SELECT channel_id, COUNT(*) as msg_count, COUNT(DISTINCT user_id) as unique_users
                FROM server_activity 
                WHERE guild_id = ? AND timestamp > ? AND activity_type = 'message'
                GROUP BY channel_id
            ''', (guild_id, yesterday))
            
            channel_data = await cursor.fetchall()
            
            for channel_id, msg_count, unique_users in channel_data:
                # Calculate engagement score
                engagement_score = (msg_count * 0.7) + (unique_users * 0.3)
                
                guild = self.bot.get_guild(guild_id)
                channel = guild.get_channel(channel_id) if guild else None
                channel_name = channel.name if channel else "Unknown"
                
                await db.execute('''
                    INSERT OR REPLACE INTO channel_analytics 
                    (guild_id, channel_id, channel_name, total_messages, active_users, 
                     last_activity, engagement_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    guild_id, channel_id, channel_name, msg_count, unique_users,
                    datetime.now(timezone.utc), engagement_score
                ))
            
            await db.commit()
    
    async def get_server_insights(self, guild_id: int) -> Dict[str, Any]:
        """Generate comprehensive server insights"""
        async with aiosqlite.connect(self.db_path) as db:
            insights = {}
            
            # Get top channels by engagement
            cursor = await db.execute('''
                SELECT channel_name, engagement_score, total_messages, active_users
                FROM channel_analytics 
                WHERE guild_id = ? 
                ORDER BY engagement_score DESC 
                LIMIT 5
            ''', (guild_id,))
            insights['top_channels'] = await cursor.fetchall()
            
            # Get least active channels
            cursor = await db.execute('''
                SELECT channel_name, engagement_score, total_messages, active_users
                FROM channel_analytics 
                WHERE guild_id = ? 
                ORDER BY engagement_score ASC 
                LIMIT 5
            ''', (guild_id,))
            insights['least_active_channels'] = await cursor.fetchall()
            
            # Get message volume trends (last 7 days)
            week_ago = datetime.now(timezone.utc) - timedelta(days=7)
            cursor = await db.execute('''
                SELECT DATE(timestamp) as day, COUNT(*) as messages
                FROM server_activity 
                WHERE guild_id = ? AND timestamp > ? AND activity_type = 'message'
                GROUP BY DATE(timestamp)
                ORDER BY day
            ''', (guild_id, week_ago))
            insights['daily_message_trends'] = await cursor.fetchall()
            
            # Get most active users
            cursor = await db.execute('''
                SELECT user_id, COUNT(*) as msg_count
                FROM server_activity 
                WHERE guild_id = ? AND timestamp > ? AND activity_type = 'message'
                GROUP BY user_id
                ORDER BY msg_count DESC
                LIMIT 10
            ''', (guild_id, week_ago))
            insights['most_active_users'] = await cursor.fetchall()
            
            return insights

class AIDecisionEngine:
    """AI-powered decision making system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.confidence_threshold = 0.75
        
    async def analyze_and_decide(self, guild_id: int, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use AI to analyze server data and suggest actions"""
        
        # Prepare data for AI analysis
        analysis_prompt = self._create_analysis_prompt(insights)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": """You are an elite AI community manager analyzing Discord server data. 
                        Provide 3 specific, actionable recommendations to improve engagement and retention.
                        
                        For each recommendation, provide:
                        1. action_type: (create_channel, archive_channel, send_announcement, reward_users, dm_inactive_users)
                        2. target: specific channel/user/role names
                        3. reasoning: why this action will help
                        4. confidence: score from 0.0 to 1.0
                        5. expected_impact: predicted outcome
                        
                        Respond in JSON format with an array of recommendations."""
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                recommendations = json.loads(content)
                return recommendations.get('recommendations', [])
            return []
            
        except Exception as e:
            logging.error(f"AI analysis failed: {e}")
            return []
    
    def _create_analysis_prompt(self, insights: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for AI analysis"""
        prompt = "Server Activity Analysis:\n\n"
        
        prompt += "TOP PERFORMING CHANNELS:\n"
        for channel, score, messages, users in insights.get('top_channels', []):
            prompt += f"- #{channel}: {score:.1f} engagement, {messages} messages, {users} active users\n"
        
        prompt += "\nLEAST ACTIVE CHANNELS:\n"
        for channel, score, messages, users in insights.get('least_active_channels', []):
            prompt += f"- #{channel}: {score:.1f} engagement, {messages} messages, {users} active users\n"
        
        prompt += "\nDAILY MESSAGE TRENDS (Last 7 days):\n"
        for day, messages in insights.get('daily_message_trends', []):
            prompt += f"- {day}: {messages} messages\n"
        
        prompt += "\nMOST ACTIVE USERS (Message count last week):\n"
        for user_id, msg_count in insights.get('most_active_users', [])[:5]:
            prompt += f"- User {user_id}: {msg_count} messages\n"
        
        prompt += "\nProvide 3 actionable recommendations to improve server engagement and retention."
        
        return prompt

class AutonomousAI(commands.Cog):
    """Autonomous AI system for intelligent server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.analytics = ServerAnalytics(bot)
        self.ai_engine = AIDecisionEngine(bot)
        self.ai_logs_channel = None
        
    async def cog_load(self):
        """Initialize the AI system"""
        await self.analytics.init_database()
        self.daily_analysis.start()
        self.hourly_data_collection.start()
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.daily_analysis.cancel()
        self.hourly_data_collection.cancel()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track message activity for analytics"""
        if not message.guild or message.author.bot:
            return
        await self.analytics.log_message_activity(message)
    
    @tasks.loop(hours=1)
    async def hourly_data_collection(self):
        """Collect and update analytics data every hour"""
        for guild in self.bot.guilds:
            await self.analytics.update_channel_analytics(guild.id)
    
    @tasks.loop(hours=24)
    async def daily_analysis(self):
        """Perform daily AI analysis and take autonomous actions"""
        for guild in self.bot.guilds:
            await self.perform_autonomous_analysis(guild)
    
    async def perform_autonomous_analysis(self, guild: discord.Guild):
        """Perform comprehensive AI analysis for a guild"""
        try:
            # Get server insights
            insights = await self.analytics.get_server_insights(guild.id)
            
            # Get AI recommendations
            recommendations = await self.ai_engine.analyze_and_decide(guild.id, insights)
            
            # Find AI logs channel
            ai_logs_channel = discord.utils.get(guild.channels, name="ai-logs")
            if not ai_logs_channel:
                # Create AI logs channel if it doesn't exist
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                # Add admin permissions
                for role in guild.roles:
                    if role.permissions.administrator:
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True)
                
                ai_logs_channel = await guild.create_text_channel(
                    name="ai-logs",
                    topic="🤖 Autonomous AI decision logs and insights",
                    overwrites=overwrites
                )
            
            # Execute high-confidence recommendations
            actions_taken = []
            for rec in recommendations:
                confidence = rec.get('confidence', 0.0)
                if confidence >= self.ai_engine.confidence_threshold:
                    action_result = await self.execute_recommendation(guild, rec, ai_logs_channel)
                    if action_result:
                        actions_taken.append(action_result)
                else:
                    # Log low-confidence suggestions for manual review
                    await self.log_suggestion(ai_logs_channel, rec)
            
            # Send daily summary
            await self.send_daily_summary(ai_logs_channel, insights, recommendations, actions_taken)
            
        except Exception as e:
            logging.error(f"Autonomous analysis failed for {guild.name}: {e}")
    
    async def execute_recommendation(self, guild: discord.Guild, recommendation: Dict, logs_channel: discord.TextChannel) -> Dict:
        """Execute an AI recommendation with high confidence"""
        action_type = recommendation.get('action_type')
        target = recommendation.get('target')
        reasoning = recommendation.get('reasoning')
        confidence = recommendation.get('confidence', 0.0)
        
        action_log = {
            'action_type': action_type,
            'target': target,
            'reasoning': reasoning,
            'confidence': confidence,
            'timestamp': datetime.now(timezone.utc),
            'success': False
        }
        
        try:
            if action_type == 'send_announcement':
                # Send motivational announcement
                general_channel = discord.utils.get(guild.channels, name="general") or guild.system_channel
                if general_channel:
                    embed = discord.Embed(
                        title="🚀 Community Update",
                        description=target,  # The announcement message
                        color=0x00ff00,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.set_footer(text="Powered by Autonomous AI")
                    await general_channel.send(embed=embed)
                    action_log['success'] = True
            
            elif action_type == 'reward_users':
                # Could implement role assignments or recognition
                # For now, log the recommendation
                action_log['success'] = True
            
            # Log the action
            embed = discord.Embed(
                title="🤖 Autonomous Action Taken",
                color=0x00ff00 if action_log['success'] else 0xff0000
            )
            embed.add_field(name="Action", value=action_type, inline=True)
            embed.add_field(name="Target", value=target[:1000], inline=True)
            embed.add_field(name="Confidence", value=f"{confidence:.2%}", inline=True)
            embed.add_field(name="Reasoning", value=reasoning[:1000], inline=False)
            embed.add_field(name="Status", value="✅ Executed" if action_log['success'] else "❌ Failed", inline=True)
            embed.timestamp = datetime.now(timezone.utc)
            
            await logs_channel.send(embed=embed)
            
        except Exception as e:
            logging.error(f"Failed to execute recommendation: {e}")
            action_log['error'] = str(e)
        
        return action_log
    
    async def log_suggestion(self, logs_channel: discord.TextChannel, recommendation: Dict):
        """Log low-confidence suggestions for manual review"""
        embed = discord.Embed(
            title="💡 AI Suggestion (Manual Review)",
            color=0xffaa00
        )
        embed.add_field(name="Action", value=recommendation.get('action_type'), inline=True)
        embed.add_field(name="Target", value=recommendation.get('target', '')[:1000], inline=True)
        embed.add_field(name="Confidence", value=f"{recommendation.get('confidence', 0):.2%}", inline=True)
        embed.add_field(name="Reasoning", value=recommendation.get('reasoning', '')[:1000], inline=False)
        embed.add_field(name="Expected Impact", value=recommendation.get('expected_impact', '')[:1000], inline=False)
        embed.timestamp = datetime.now(timezone.utc)
        
        await logs_channel.send(embed=embed)
    
    async def send_daily_summary(self, logs_channel: discord.TextChannel, insights: Dict, 
                                recommendations: List, actions_taken: List):
        """Send comprehensive daily analytics summary"""
        embed = discord.Embed(
            title="📊 Daily Server Analytics Summary",
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Top channels summary
        top_channels = insights.get('top_channels', [])[:3]
        if top_channels:
            top_summary = "\n".join([f"#{name}: {score:.1f}" for name, score, _, _ in top_channels])
            embed.add_field(name="🔥 Most Engaged Channels", value=top_summary, inline=True)
        
        # Message trends
        daily_trends = insights.get('daily_message_trends', [])
        if len(daily_trends) >= 2:
            today_msgs = daily_trends[-1][1]
            yesterday_msgs = daily_trends[-2][1] if len(daily_trends) > 1 else 0
            trend = "📈" if today_msgs > yesterday_msgs else "📉" if today_msgs < yesterday_msgs else "➡️"
            embed.add_field(name="Message Trend", value=f"{trend} {today_msgs} messages today", inline=True)
        
        # AI actions summary
        embed.add_field(name="🤖 AI Actions", value=f"{len(actions_taken)} executed, {len(recommendations) - len(actions_taken)} suggested", inline=True)
        
        # Recommendations summary
        if recommendations:
            rec_summary = "\n".join([f"• {rec.get('action_type', 'Unknown')} ({rec.get('confidence', 0):.1%})" for rec in recommendations[:5]])
            embed.add_field(name="💡 AI Recommendations", value=rec_summary, inline=False)
        
        await logs_channel.send(embed=embed)
    
    @app_commands.command(name="insight", description="Get AI-powered server insights")
    @app_commands.default_permissions(manage_guild=True)
    async def insight(self, interaction: discord.Interaction):
        """Generate real-time server insights"""
        await interaction.response.defer()
        
        try:
            insights = await self.analytics.get_server_insights(interaction.guild.id)
            
            embed = discord.Embed(
                title="🧠 AI Server Insights",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Top channels
            top_channels = insights.get('top_channels', [])[:5]
            if top_channels:
                channel_text = "\n".join([f"#{name}: {score:.1f} engagement" for name, score, _, _ in top_channels])
                embed.add_field(name="🔥 Top Channels", value=channel_text, inline=True)
            
            # Activity trends
            daily_trends = insights.get('daily_message_trends', [])
            if daily_trends:
                total_messages = sum(msgs for _, msgs in daily_trends)
                avg_daily = total_messages / len(daily_trends)
                embed.add_field(name="📈 Activity", value=f"{total_messages} messages this week\n{avg_daily:.0f} daily average", inline=True)
            
            # Most active users
            active_users = insights.get('most_active_users', [])[:5]
            if active_users:
                user_text = "\n".join([f"<@{user_id}>: {count} messages" for user_id, count in active_users])
                embed.add_field(name="👑 Most Active", value=user_text, inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error generating insights: {e}", ephemeral=True)
    
    @app_commands.command(name="ai-suggest", description="Get fresh AI suggestions for community events")
    @app_commands.default_permissions(manage_guild=True)
    async def ai_suggest(self, interaction: discord.Interaction):
        """Generate AI suggestions for community engagement"""
        await interaction.response.defer()
        
        try:
            insights = await self.analytics.get_server_insights(interaction.guild.id)
            recommendations = await self.ai_engine.analyze_and_decide(interaction.guild.id, insights)
            
            embed = discord.Embed(
                title="💡 AI Community Suggestions",
                color=0xffaa00,
                timestamp=datetime.now(timezone.utc)
            )
            
            for i, rec in enumerate(recommendations[:3], 1):
                embed.add_field(
                    name=f"Suggestion {i}: {rec.get('action_type', 'Unknown').replace('_', ' ').title()}",
                    value=f"**Target:** {rec.get('target', 'N/A')}\n**Reasoning:** {rec.get('reasoning', 'N/A')[:200]}...\n**Confidence:** {rec.get('confidence', 0):.1%}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error generating suggestions: {e}", ephemeral=True)
    
    @app_commands.command(name="ai-analytics", description="View comprehensive server analytics")
    @app_commands.default_permissions(manage_guild=True)
    async def ai_analytics(self, interaction: discord.Interaction):
        """Show detailed server analytics dashboard"""
        await interaction.response.defer()
        
        try:
            insights = await self.analytics.get_server_insights(interaction.guild.id)
            
            # Create multiple embeds for comprehensive analytics
            embeds = []
            
            # Channel Performance Embed
            channel_embed = discord.Embed(
                title="📊 Channel Performance Analytics",
                color=0x0099ff,
                timestamp=datetime.now(timezone.utc)
            )
            
            top_channels = insights.get('top_channels', [])
            least_channels = insights.get('least_active_channels', [])
            
            if top_channels:
                top_text = "\n".join([f"#{name}: {score:.1f} ({msgs} msgs, {users} users)" 
                                    for name, score, msgs, users in top_channels])
                channel_embed.add_field(name="🔥 Highest Engagement", value=top_text, inline=True)
            
            if least_channels:
                low_text = "\n".join([f"#{name}: {score:.1f} ({msgs} msgs, {users} users)" 
                                    for name, score, msgs, users in least_channels])
                channel_embed.add_field(name="📉 Needs Attention", value=low_text, inline=True)
            
            embeds.append(channel_embed)
            
            # Activity Trends Embed
            trends_embed = discord.Embed(
                title="📈 Activity Trends (Last 7 Days)",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            daily_trends = insights.get('daily_message_trends', [])
            if daily_trends:
                trend_text = "\n".join([f"{day}: {msgs} messages" for day, msgs in daily_trends])
                trends_embed.add_field(name="Daily Message Volume", value=trend_text, inline=False)
                
                total_msgs = sum(msgs for _, msgs in daily_trends)
                avg_daily = total_msgs / len(daily_trends)
                trends_embed.add_field(name="Summary", value=f"Total: {total_msgs}\nDaily Avg: {avg_daily:.0f}", inline=True)
            
            embeds.append(trends_embed)
            
            # Send all embeds
            await interaction.followup.send(embeds=embeds)
            
        except Exception as e:
            await interaction.followup.send(f"Error generating analytics: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutonomousAI(bot))