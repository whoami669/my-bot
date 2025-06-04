import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import logging
import os
from openai import OpenAI
import random

class PromotionalContentGenerator:
    """AI-powered promotional content generation system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.db_path = 'promotional_data.db'
        
    async def init_promotional_database(self):
        """Initialize promotional content database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Generated content tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS generated_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    content_type TEXT,
                    platform TEXT,
                    content_text TEXT,
                    hashtags TEXT,
                    image_prompt TEXT,
                    generated_at DATETIME,
                    used BOOLEAN DEFAULT 0,
                    performance_score REAL DEFAULT 0.0
                )
            ''')
            
            # Invite tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS invite_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    inviter_id INTEGER,
                    invited_user_id INTEGER,
                    invite_code TEXT,
                    joined_at DATETIME,
                    still_member BOOLEAN DEFAULT 1
                )
            ''')
            
            # Growth campaigns
            await db.execute('''
                CREATE TABLE IF NOT EXISTS growth_campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    campaign_name TEXT,
                    campaign_type TEXT,
                    target_invites INTEGER,
                    reward_description TEXT,
                    start_date DATETIME,
                    end_date DATETIME,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Server highlights
            await db.execute('''
                CREATE TABLE IF NOT EXISTS server_highlights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    highlight_type TEXT,
                    description TEXT,
                    timestamp DATETIME,
                    metrics TEXT,
                    converted_to_promo BOOLEAN DEFAULT 0
                )
            ''')
            
            await db.commit()
    
    async def generate_promotional_content(self, guild: discord.Guild, platform: str, content_type: str = "general") -> Dict[str, Any]:
        """Generate AI-powered promotional content for specific platforms"""
        
        # Gather server data for context
        server_context = await self._gather_server_context(guild)
        
        # Create platform-specific prompt
        prompt = self._create_promotional_prompt(server_context, platform, content_type)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert Discord growth marketer and social media strategist. 
                        Create compelling promotional content for {platform} that drives server growth and engagement.
                        
                        Consider platform-specific best practices:
                        - Reddit: Authentic, community-focused, detailed descriptions
                        - TikTok: Short, catchy, trending language with emojis
                        - Twitter/X: Concise, hashtag-optimized, engaging hooks
                        - Instagram: Visual-focused, lifestyle-oriented, hashtag-heavy
                        
                        Respond in JSON format with:
                        {{
                            "caption": "Main promotional text",
                            "hashtags": ["list", "of", "relevant", "hashtags"],
                            "image_prompt": "DALL-E prompt for promotional image",
                            "call_to_action": "Specific CTA",
                            "platform_notes": "Platform-specific optimization tips"
                        }}"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            if content:
                promo_data = json.loads(content)
                
                # Store generated content
                await self._store_generated_content(guild.id, content_type, platform, promo_data)
                
                return promo_data
            return {}
            
        except Exception as e:
            logging.error(f"Promotional content generation failed: {e}")
            return {}
    
    async def _gather_server_context(self, guild: discord.Guild) -> Dict[str, Any]:
        """Gather comprehensive server context for promotional content"""
        context = {
            'server_name': guild.name,
            'member_count': guild.member_count,
            'boost_level': guild.premium_tier,
            'boost_count': guild.premium_subscription_count or 0,
            'channel_count': len(guild.text_channels),
            'voice_channels': len(guild.voice_channels),
            'roles_count': len(guild.roles),
            'features': []
        }
        
        # Analyze server features
        if guild.premium_tier > 0:
            context['features'].append(f"Level {guild.premium_tier} Boosted Server")
        
        # Check for special channels
        special_channels = []
        for channel in guild.text_channels:
            if any(keyword in channel.name.lower() for keyword in ['game', 'music', 'art', 'meme', 'event']):
                special_channels.append(channel.name)
        
        context['special_channels'] = special_channels[:5]  # Top 5 special channels
        
        # Check for bots and features
        bot_count = sum(1 for member in guild.members if member.bot)
        context['bot_features'] = bot_count > 5  # Indicates feature-rich server
        
        return context
    
    def _create_promotional_prompt(self, server_context: Dict, platform: str, content_type: str) -> str:
        """Create platform-specific promotional prompt"""
        prompt = f"Create promotional content for {platform} for this Discord server:\n\n"
        
        prompt += f"SERVER DETAILS:\n"
        prompt += f"Name: {server_context['server_name']}\n"
        prompt += f"Members: {server_context['member_count']}\n"
        prompt += f"Boost Level: {server_context['boost_level']}\n"
        prompt += f"Features: {', '.join(server_context['features'])}\n"
        
        if server_context['special_channels']:
            prompt += f"Special Channels: {', '.join(server_context['special_channels'])}\n"
        
        # Content type specific instructions
        if content_type == "event":
            prompt += f"\nContent Type: Event Promotion - Focus on upcoming events, community activities, and FOMO\n"
        elif content_type == "milestone":
            prompt += f"\nContent Type: Milestone Celebration - Celebrate growth, achievements, and community wins\n"
        elif content_type == "feature":
            prompt += f"\nContent Type: Feature Highlight - Showcase unique server features and benefits\n"
        else:
            prompt += f"\nContent Type: General Promotion - Overall server benefits and community appeal\n"
        
        # Platform-specific instructions
        platform_instructions = {
            "reddit": "Focus on authentic community benefits, avoid overly promotional language, include detailed descriptions",
            "tiktok": "Use trending language, lots of emojis, short punchy phrases, youth-oriented appeal",
            "twitter": "Concise and engaging, use relevant hashtags, create urgency or FOMO",
            "instagram": "Visual-focused, lifestyle appeal, use Instagram-style hashtags and engaging captions"
        }
        
        prompt += f"\nPlatform Guidelines: {platform_instructions.get(platform.lower(), 'General social media best practices')}\n"
        prompt += f"\nCreate content that drives immediate action and server joins."
        
        return prompt
    
    async def _store_generated_content(self, guild_id: int, content_type: str, platform: str, promo_data: Dict):
        """Store generated promotional content"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO generated_content 
                (guild_id, content_type, platform, content_text, hashtags, image_prompt, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                guild_id,
                content_type,
                platform,
                promo_data.get('caption', ''),
                json.dumps(promo_data.get('hashtags', [])),
                promo_data.get('image_prompt', ''),
                datetime.now(timezone.utc)
            ))
            await db.commit()
    
    async def generate_dalle_image(self, image_prompt: str) -> Optional[str]:
        """Generate promotional image using DALL-E"""
        try:
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=f"Professional Discord server promotional image: {image_prompt}",
                size="1024x1024",
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            logging.error(f"DALL-E image generation failed: {e}")
            return None

class InviteTracker:
    """Advanced invite tracking and growth gamification"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'promotional_data.db'
        self.invite_cache = {}
    
    async def setup_invite_tracking(self, guild: discord.Guild):
        """Setup invite tracking for a guild"""
        try:
            invites = await guild.invites()
            self.invite_cache[guild.id] = {invite.code: invite.uses for invite in invites}
        except discord.Forbidden:
            logging.warning(f"Missing permissions to view invites in {guild.name}")
    
    async def track_new_member(self, member: discord.Member):
        """Track which invite was used for new member"""
        guild = member.guild
        
        try:
            current_invites = await guild.invites()
            cached_invites = self.invite_cache.get(guild.id, {})
            
            # Find which invite was used
            for invite in current_invites:
                cached_uses = cached_invites.get(invite.code, 0)
                if invite.uses > cached_uses:
                    # This invite was used
                    await self._record_invite_use(guild.id, invite.inviter.id, member.id, invite.code)
                    await self._update_inviter_rewards(guild, invite.inviter)
                    
                    # Update cache
                    cached_invites[invite.code] = invite.uses
                    break
            
            self.invite_cache[guild.id] = {invite.code: invite.uses for invite in current_invites}
            
        except discord.Forbidden:
            logging.warning(f"Cannot track invites in {guild.name} - missing permissions")
    
    async def _record_invite_use(self, guild_id: int, inviter_id: int, invited_user_id: int, invite_code: str):
        """Record invite usage in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO invite_tracking 
                (guild_id, inviter_id, invited_user_id, invite_code, joined_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (guild_id, inviter_id, invited_user_id, invite_code, datetime.now(timezone.utc)))
            await db.commit()
    
    async def _update_inviter_rewards(self, guild: discord.Guild, inviter: discord.Member):
        """Update rewards for successful inviter"""
        # Get invite count for user
        invite_count = await self.get_user_invite_count(guild.id, inviter.id)
        
        # Award roles based on invite milestones
        if invite_count == 5:
            await self._award_invite_role(guild, inviter, "Recruiter", "🎯")
        elif invite_count == 10:
            await self._award_invite_role(guild, inviter, "Growth Champion", "🚀")
        elif invite_count == 25:
            await self._award_invite_role(guild, inviter, "Community Builder", "🏗️")
    
    async def _award_invite_role(self, guild: discord.Guild, member: discord.Member, role_name: str, emoji: str):
        """Award special role for invite milestones"""
        try:
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                # Create the role
                role = await guild.create_role(
                    name=role_name,
                    color=discord.Color.gold(),
                    reason="Invite milestone reward"
                )
            
            await member.add_roles(role)
            
            # Announce achievement
            announcement_channel = discord.utils.get(guild.channels, name="general") or guild.system_channel
            if announcement_channel:
                embed = discord.Embed(
                    title=f"{emoji} Invite Champion!",
                    description=f"🎉 {member.mention} has earned the **{role_name}** role for their amazing invite contributions!",
                    color=discord.Color.gold(),
                    timestamp=datetime.now(timezone.utc)
                )
                await announcement_channel.send(embed=embed)
                
        except discord.Forbidden:
            logging.warning(f"Cannot award role in {guild.name} - missing permissions")
    
    async def get_user_invite_count(self, guild_id: int, user_id: int) -> int:
        """Get total invite count for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM invite_tracking 
                WHERE guild_id = ? AND inviter_id = ? AND still_member = 1
            ''', (guild_id, user_id))
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def get_invite_leaderboard(self, guild_id: int, limit: int = 10) -> List[tuple]:
        """Get invite leaderboard for guild"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT inviter_id, COUNT(*) as invite_count
                FROM invite_tracking 
                WHERE guild_id = ? AND still_member = 1
                GROUP BY inviter_id
                ORDER BY invite_count DESC
                LIMIT ?
            ''', (guild_id, limit))
            return await cursor.fetchall()

class PromotionalEngine(commands.Cog):
    """Comprehensive promotional and growth system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.content_generator = PromotionalContentGenerator(bot)
        self.invite_tracker = InviteTracker(bot)
        
    async def cog_load(self):
        """Initialize promotional systems"""
        await self.content_generator.init_promotional_database()
        
        # Setup invite tracking for all guilds
        for guild in self.bot.guilds:
            await self.invite_tracker.setup_invite_tracking(guild)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track invite usage when members join"""
        await self.invite_tracker.track_new_member(member)
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Setup invite tracking for new guilds"""
        await self.invite_tracker.setup_invite_tracking(guild)
    
    @app_commands.command(name="promote", description="Generate AI-powered promotional content for social media")
    @app_commands.describe(
        platform="Social media platform (reddit, tiktok, twitter, instagram)",
        content_type="Type of promotional content (general, event, milestone, feature)"
    )
    @app_commands.choices(platform=[
        app_commands.Choice(name="Reddit", value="reddit"),
        app_commands.Choice(name="TikTok", value="tiktok"),
        app_commands.Choice(name="Twitter/X", value="twitter"),
        app_commands.Choice(name="Instagram", value="instagram")
    ])
    @app_commands.choices(content_type=[
        app_commands.Choice(name="General Promotion", value="general"),
        app_commands.Choice(name="Event Promotion", value="event"),
        app_commands.Choice(name="Milestone Celebration", value="milestone"),
        app_commands.Choice(name="Feature Highlight", value="feature")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def promote(self, interaction: discord.Interaction, platform: str, content_type: str = "general"):
        """Generate promotional content for social media platforms"""
        await interaction.response.defer()
        
        try:
            # Generate promotional content
            promo_content = await self.content_generator.generate_promotional_content(
                interaction.guild, platform, content_type
            )
            
            if not promo_content:
                await interaction.followup.send("Failed to generate promotional content. Please try again.", ephemeral=True)
                return
            
            # Create promotional embed
            embed = discord.Embed(
                title=f"🚀 {platform.title()} Promotional Content",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Main content
            caption = promo_content.get('caption', '')
            embed.add_field(name="📝 Caption", value=caption[:1000], inline=False)
            
            # Hashtags
            hashtags = promo_content.get('hashtags', [])
            if hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
                embed.add_field(name="🏷️ Hashtags", value=hashtag_text[:1000], inline=False)
            
            # Call to action
            cta = promo_content.get('call_to_action', '')
            if cta:
                embed.add_field(name="📢 Call to Action", value=cta, inline=False)
            
            # Platform notes
            notes = promo_content.get('platform_notes', '')
            if notes:
                embed.add_field(name="💡 Platform Tips", value=notes[:1000], inline=False)
            
            # Image prompt
            image_prompt = promo_content.get('image_prompt', '')
            if image_prompt:
                embed.add_field(name="🎨 Image Prompt (for DALL-E)", value=image_prompt[:1000], inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Try to generate image
            if image_prompt:
                image_url = await self.content_generator.generate_dalle_image(image_prompt)
                if image_url:
                    image_embed = discord.Embed(
                        title="🎨 Generated Promotional Image",
                        color=0xff6b6b
                    )
                    image_embed.set_image(url=image_url)
                    await interaction.followup.send(embed=image_embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error generating promotional content: {e}", ephemeral=True)
    
    @app_commands.command(name="invite-leaderboard", description="View server invite leaderboard")
    async def invite_leaderboard(self, interaction: discord.Interaction):
        """Display invite leaderboard"""
        await interaction.response.defer()
        
        try:
            leaderboard = await self.invite_tracker.get_invite_leaderboard(interaction.guild.id)
            
            embed = discord.Embed(
                title="🏆 Invite Champions Leaderboard",
                color=0xffd700,
                timestamp=datetime.now(timezone.utc)
            )
            
            if not leaderboard:
                embed.description = "No invite data available yet. Start inviting friends to see the leaderboard!"
            else:
                leaderboard_text = ""
                medals = ["🥇", "🥈", "🥉"]
                
                for i, (user_id, invite_count) in enumerate(leaderboard):
                    user = interaction.guild.get_member(user_id)
                    username = user.display_name if user else f"User {user_id}"
                    medal = medals[i] if i < 3 else "🏅"
                    leaderboard_text += f"{medal} **{username}**: {invite_count} invites\n"
                
                embed.description = leaderboard_text
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error fetching invite leaderboard: {e}", ephemeral=True)
    
    @app_commands.command(name="my-invites", description="Check your invite statistics")
    async def my_invites(self, interaction: discord.Interaction):
        """Show user's invite statistics"""
        await interaction.response.defer()
        
        try:
            invite_count = await self.invite_tracker.get_user_invite_count(
                interaction.guild.id, interaction.user.id
            )
            
            embed = discord.Embed(
                title="📊 Your Invite Statistics",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(name="🎯 Total Invites", value=str(invite_count), inline=True)
            
            # Show next milestone
            milestones = [5, 10, 25, 50, 100]
            next_milestone = next((m for m in milestones if m > invite_count), None)
            
            if next_milestone:
                remaining = next_milestone - invite_count
                embed.add_field(name="🎁 Next Reward", value=f"{remaining} more invites to reach {next_milestone}!", inline=True)
            else:
                embed.add_field(name="🏆 Status", value="Champion Inviter!", inline=True)
            
            # Show rewards earned
            rewards = []
            if invite_count >= 5:
                rewards.append("🎯 Recruiter")
            if invite_count >= 10:
                rewards.append("🚀 Growth Champion")
            if invite_count >= 25:
                rewards.append("🏗️ Community Builder")
            
            if rewards:
                embed.add_field(name="🎖️ Rewards Earned", value="\n".join(rewards), inline=False)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error fetching invite statistics: {e}", ephemeral=True)
    
    @app_commands.command(name="setup-promotion", description="Setup promotional channels and features")
    @app_commands.default_permissions(administrator=True)
    async def setup_promotion(self, interaction: discord.Interaction):
        """Setup promotional channels and features"""
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            channels_created = []
            
            # Create promotional channels
            promo_channels = [
                ("invite-friends", "🤝 Invite your friends and get rewarded!"),
                ("share-this-server", "📢 Share our awesome server on social media"),
                ("growth-announcements", "🚀 Server growth milestones and celebrations")
            ]
            
            for channel_name, topic in promo_channels:
                existing = discord.utils.get(guild.channels, name=channel_name)
                if not existing:
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        topic=topic
                    )
                    channels_created.append(channel.name)
            
            embed = discord.Embed(
                title="✅ Promotional System Setup Complete",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            if channels_created:
                embed.add_field(
                    name="📺 Channels Created",
                    value="\n".join([f"#{name}" for name in channels_created]),
                    inline=False
                )
            
            embed.add_field(
                name="🎯 Features Enabled",
                value="• Invite tracking and rewards\n• Promotional content generation\n• Growth gamification\n• Leaderboards",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Commands Available",
                value="`/promote` - Generate social media content\n`/invite-leaderboard` - View top inviters\n`/my-invites` - Check personal stats",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Error setting up promotional system: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PromotionalEngine(bot))