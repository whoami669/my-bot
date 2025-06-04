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
import subprocess
import aiohttp
import aiofiles
from pathlib import Path
import random

class ViralContentScraper:
    """Advanced viral content discovery and downloading system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'viral_content.db'
        self.download_dir = 'viral_streamer_clips'
        self.supported_platforms = ['twitter', 'youtube', 'twitch']
        
    async def init_content_database(self):
        """Initialize viral content tracking database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Downloaded content tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS downloaded_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    platform TEXT,
                    original_url TEXT UNIQUE,
                    local_path TEXT,
                    title TEXT,
                    engagement_score INTEGER,
                    download_date DATETIME,
                    uploaded_to_tiktok BOOLEAN DEFAULT 0,
                    caption_used TEXT,
                    performance_metrics TEXT
                )
            ''')
            
            # Content search keywords
            await db.execute('''
                CREATE TABLE IF NOT EXISTS search_keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    keyword TEXT,
                    platform TEXT,
                    min_engagement INTEGER DEFAULT 100,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Upload queue
            await db.execute('''
                CREATE TABLE IF NOT EXISTS upload_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    content_id INTEGER,
                    scheduled_time DATETIME,
                    custom_caption TEXT,
                    status TEXT DEFAULT 'pending',
                    upload_attempt_count INTEGER DEFAULT 0,
                    FOREIGN KEY (content_id) REFERENCES downloaded_content (id)
                )
            ''')
            
            # Performance tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS content_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    tracked_date DATETIME,
                    FOREIGN KEY (content_id) REFERENCES downloaded_content (id)
                )
            ''')
            
            await db.commit()
    
    async def search_viral_content(self, platform: str, keywords: List[str], min_engagement: int = 100) -> List[Dict]:
        """Search for viral content on specified platform"""
        results = []
        
        try:
            if platform.lower() == 'twitter':
                results = await self._search_twitter_content(keywords, min_engagement)
            elif platform.lower() == 'youtube':
                results = await self._search_youtube_content(keywords, min_engagement)
            elif platform.lower() == 'twitch':
                results = await self._search_twitch_content(keywords, min_engagement)
            
            return results
            
        except Exception as e:
            logging.error(f"Content search failed for {platform}: {e}")
            return []
    
    async def _search_twitter_content(self, keywords: List[str], min_engagement: int) -> List[Dict]:
        """Search Twitter/X for viral content"""
        # This would use Twitter API v2 or web scraping
        # For demonstration, returning mock structure
        search_results = []
        
        for keyword in keywords:
            # In real implementation, would use Twitter API or snscrape
            query = f"{keyword} filter:videos min_faves:{min_engagement} lang:en"
            
            # Mock results structure - replace with actual API calls
            mock_results = [
                {
                    'url': f'https://twitter.com/example/status/123456789_{keyword}',
                    'title': f'Viral {keyword} clip',
                    'engagement': min_engagement + random.randint(50, 500),
                    'platform': 'twitter',
                    'video_url': f'https://video.twimg.com/ext_tw_video/{keyword}.mp4',
                    'thumbnail': f'https://pbs.twimg.com/media/{keyword}.jpg'
                }
            ]
            search_results.extend(mock_results)
        
        return search_results
    
    async def _search_youtube_content(self, keywords: List[str], min_engagement: int) -> List[Dict]:
        """Search YouTube for viral content"""
        # Would use YouTube Data API v3
        return []
    
    async def _search_twitch_content(self, keywords: List[str], min_engagement: int) -> List[Dict]:
        """Search Twitch for viral clips"""
        # Would use Twitch API
        return []
    
    async def download_content(self, content_data: Dict, download_path: str) -> Optional[str]:
        """Download viral content using yt-dlp"""
        try:
            # Ensure download directory exists
            Path(download_path).mkdir(parents=True, exist_ok=True)
            
            url = content_data.get('url', '')
            if not url:
                return None
            
            # Create filename
            safe_title = "".join(c for c in content_data.get('title', 'video') if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            full_path = os.path.join(download_path, filename)
            
            # Download using yt-dlp
            cmd = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--output', full_path,
                '--no-playlist',
                '--extract-flat',
                url
            ]
            
            # Run download command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(full_path):
                return full_path
            else:
                logging.error(f"Download failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logging.error(f"Content download error: {e}")
            return None
    
    async def store_downloaded_content(self, guild_id: int, content_data: Dict, local_path: str):
        """Store downloaded content information in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO downloaded_content 
                (guild_id, platform, original_url, local_path, title, engagement_score, download_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                guild_id,
                content_data.get('platform', 'unknown'),
                content_data.get('url', ''),
                local_path,
                content_data.get('title', ''),
                content_data.get('engagement', 0),
                datetime.now(timezone.utc)
            ))
            await db.commit()

class TikTokUploader:
    """TikTok upload automation using browser automation"""
    
    def __init__(self):
        self.upload_dir = 'viral_streamer_clips'
        self.captions_templates = [
            "This streamer went CRAZY 😱🔥 #streamer #fyp #viral #gaming",
            "NO WAY this actually happened 🤯 #gaming #streamer #clips #fyp",
            "When streamers lose their minds 😂 #funny #gaming #streamer #viral",
            "This clip broke the internet 🌐💥 #viral #gaming #streamer #fyp",
            "Peak gaming content right here 🎮🔥 #gaming #streamer #clips #viral"
        ]
    
    async def prepare_upload_script(self, video_path: str, caption: str = None) -> str:
        """Generate Playwright script for TikTok upload"""
        if not caption:
            caption = random.choice(self.captions_templates)
        
        script = f'''
import asyncio
from playwright.async_api import async_playwright
import os

async def upload_to_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # Load saved cookies if available
        try:
            await context.add_cookies([
                # Add your TikTok session cookies here
                # Get these by logging in manually and saving cookies
            ])
        except:
            pass
        
        page = await context.new_page()
        
        try:
            # Navigate to TikTok upload page
            await page.goto('https://www.tiktok.com/upload?lang=en')
            await page.wait_for_timeout(3000)
            
            # Check if login is needed
            if page.url.find('login') != -1:
                print("Please login manually and save cookies")
                await page.wait_for_timeout(30000)  # Wait for manual login
            
            # Upload video file
            await page.set_input_files('input[type="file"]', '{video_path}')
            await page.wait_for_timeout(5000)
            
            # Add caption
            caption_input = page.locator('[data-text="true"]').first
            await caption_input.fill('{caption}')
            
            # Wait for processing
            await page.wait_for_timeout(10000)
            
            # Click post button
            post_button = page.locator('button:has-text("Post")')
            await post_button.click()
            
            print("Upload completed successfully!")
            
        except Exception as e:
            print(f"Upload failed: {{e}}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(upload_to_tiktok())
'''
        return script
    
    async def generate_custom_caption(self, content_data: Dict) -> str:
        """Generate AI-powered custom caption for content"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            prompt = f"""Create a viral TikTok caption for this gaming/streamer content:
            
            Title: {content_data.get('title', 'Gaming clip')}
            Platform: {content_data.get('platform', 'unknown')}
            Engagement: {content_data.get('engagement', 0)} interactions
            
            Requirements:
            - Use trending gaming hashtags
            - Create FOMO/excitement
            - Keep under 100 characters
            - Include relevant emojis
            - Make it shareable
            
            Return just the caption text."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Caption generation failed: {e}")
            return random.choice(self.captions_templates)

class ViralContentAutomation(commands.Cog):
    """Complete viral content automation system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scraper = ViralContentScraper(bot)
        self.uploader = TikTokUploader()
        
    async def cog_load(self):
        """Initialize the viral content system"""
        await self.scraper.init_content_database()
        # Start automated content discovery
        # self.daily_content_discovery.start()  # Uncomment to enable automation
    
    @tasks.loop(hours=12)  # Run twice daily
    async def daily_content_discovery(self):
        """Automated viral content discovery and download"""
        for guild in self.bot.guilds:
            await self.discover_and_download_content(guild)
    
    async def discover_and_download_content(self, guild: discord.Guild):
        """Discover and download viral content for a guild"""
        try:
            # Default search keywords
            keywords = ['streamer clip', 'gaming fail', 'epic gaming moment', 'twitch clip', 'funny gaming']
            
            # Search for viral content
            for platform in ['twitter']:  # Start with Twitter
                results = await self.scraper.search_viral_content(platform, keywords, min_engagement=100)
                
                for content in results[:3]:  # Limit to 3 per platform
                    # Create download directory
                    today = datetime.now().strftime('%Y-%m-%d')
                    download_path = os.path.join(self.scraper.download_dir, str(guild.id), today)
                    
                    # Download content
                    local_path = await self.scraper.download_content(content, download_path)
                    
                    if local_path:
                        # Store in database
                        await self.scraper.store_downloaded_content(guild.id, content, local_path)
                        
                        # Notify admins
                        await self.notify_content_downloaded(guild, content, local_path)
        
        except Exception as e:
            logging.error(f"Content discovery failed for {guild.name}: {e}")
    
    async def notify_content_downloaded(self, guild: discord.Guild, content: Dict, local_path: str):
        """Notify admins about downloaded content"""
        # Find notification channel
        channel = discord.utils.get(guild.channels, name="viral-content-logs")
        if not channel:
            return
        
        embed = discord.Embed(
            title="🔥 Viral Content Downloaded",
            color=0xff6b6b,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="Platform", value=content.get('platform', 'Unknown'), inline=True)
        embed.add_field(name="Engagement", value=f"{content.get('engagement', 0)} interactions", inline=True)
        embed.add_field(name="Title", value=content.get('title', 'Unknown')[:100], inline=False)
        embed.add_field(name="Local Path", value=local_path, inline=False)
        
        await channel.send(embed=embed)
    
    @app_commands.command(name="search-viral-content", description="Search for viral gaming/streamer content")
    @app_commands.describe(
        platform="Platform to search (twitter, youtube, twitch)",
        keywords="Search keywords (comma separated)",
        min_engagement="Minimum engagement threshold"
    )
    @app_commands.choices(platform=[
        app_commands.Choice(name="Twitter/X", value="twitter"),
        app_commands.Choice(name="YouTube", value="youtube"),
        app_commands.Choice(name="Twitch", value="twitch")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def search_viral_content(
        self, 
        interaction: discord.Interaction, 
        platform: str, 
        keywords: str, 
        min_engagement: int = 100
    ):
        """Search for viral content on specified platform"""
        await interaction.response.defer()
        
        try:
            keyword_list = [kw.strip() for kw in keywords.split(',')]
            results = await self.scraper.search_viral_content(platform, keyword_list, min_engagement)
            
            if not results:
                await interaction.followup.send(f"No viral content found for keywords: {keywords}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title=f"🔍 Viral Content Search Results - {platform.title()}",
                color=0x00ff99,
                timestamp=datetime.now(timezone.utc)
            )
            
            for i, content in enumerate(results[:5], 1):
                embed.add_field(
                    name=f"Result {i}: {content.get('title', 'Unknown')[:50]}",
                    value=f"**Engagement:** {content.get('engagement', 0)}\n**URL:** {content.get('url', 'N/A')[:100]}",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Search failed: {e}", ephemeral=True)
    
    @app_commands.command(name="download-viral-content", description="Download viral content from URL")
    @app_commands.describe(url="URL of the viral content to download")
    @app_commands.default_permissions(manage_guild=True)
    async def download_viral_content(self, interaction: discord.Interaction, url: str):
        """Download viral content from provided URL"""
        await interaction.response.defer()
        
        try:
            # Create content data
            content_data = {
                'url': url,
                'title': f'Manual_Download_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'platform': 'manual',
                'engagement': 0
            }
            
            # Create download directory
            today = datetime.now().strftime('%Y-%m-%d')
            download_path = os.path.join(self.scraper.download_dir, str(interaction.guild.id), today)
            
            # Download content
            local_path = await self.scraper.download_content(content_data, download_path)
            
            if local_path:
                # Store in database
                await self.scraper.store_downloaded_content(interaction.guild.id, content_data, local_path)
                
                embed = discord.Embed(
                    title="✅ Content Downloaded Successfully",
                    color=0x00ff99,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Source URL", value=url, inline=False)
                embed.add_field(name="Local Path", value=local_path, inline=False)
                embed.add_field(name="File Size", value=f"{os.path.getsize(local_path) / (1024*1024):.1f} MB", inline=True)
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Failed to download content. Please check the URL and try again.", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Download failed: {e}", ephemeral=True)
    
    @app_commands.command(name="generate-tiktok-script", description="Generate TikTok upload script for downloaded content")
    @app_commands.describe(content_title="Title or partial name of downloaded content")
    @app_commands.default_permissions(manage_guild=True)
    async def generate_tiktok_script(self, interaction: discord.Interaction, content_title: str):
        """Generate Playwright script for TikTok upload"""
        await interaction.response.defer()
        
        try:
            # Find matching content in database
            async with aiosqlite.connect(self.scraper.db_path) as db:
                cursor = await db.execute('''
                    SELECT * FROM downloaded_content 
                    WHERE guild_id = ? AND title LIKE ? 
                    ORDER BY download_date DESC LIMIT 1
                ''', (interaction.guild.id, f'%{content_title}%'))
                
                content_row = await cursor.fetchone()
                
                if not content_row:
                    await interaction.followup.send(f"No downloaded content found matching: {content_title}", ephemeral=True)
                    return
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                content_data = dict(zip(columns, content_row))
                
                # Generate custom caption
                caption = await self.uploader.generate_custom_caption(content_data)
                
                # Generate upload script
                script = await self.uploader.prepare_upload_script(content_data['local_path'], caption)
                
                # Save script to file
                script_filename = f"tiktok_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
                script_path = os.path.join(self.scraper.download_dir, str(interaction.guild.id), script_filename)
                
                os.makedirs(os.path.dirname(script_path), exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script)
                
                embed = discord.Embed(
                    title="🎬 TikTok Upload Script Generated",
                    color=0xff6b6b,
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Content", value=content_data['title'], inline=False)
                embed.add_field(name="Generated Caption", value=caption, inline=False)
                embed.add_field(name="Script Path", value=script_path, inline=False)
                embed.add_field(
                    name="Instructions", 
                    value="1. Install playwright: `pip install playwright`\n2. Run: `python " + script_filename + "`\n3. Login to TikTok when prompted\n4. Script will handle the upload", 
                    inline=False
                )
                
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Script generation failed: {e}", ephemeral=True)
    
    @app_commands.command(name="setup-viral-automation", description="Setup viral content automation system")
    @app_commands.default_permissions(administrator=True)
    async def setup_viral_automation(self, interaction: discord.Interaction):
        """Setup viral content automation channels and features"""
        await interaction.response.defer()
        
        try:
            guild = interaction.guild
            channels_created = []
            
            # Create viral content channels
            viral_channels = [
                ("viral-content-logs", "🔥 Automated viral content discovery logs"),
                ("tiktok-queue", "📱 TikTok upload queue and scheduling"),
                ("content-performance", "📊 Track performance of uploaded content")
            ]
            
            for channel_name, topic in viral_channels:
                existing = discord.utils.get(guild.channels, name=channel_name)
                if not existing:
                    channel = await guild.create_text_channel(
                        name=channel_name,
                        topic=topic
                    )
                    channels_created.append(channel.name)
            
            # Create download directory
            download_path = os.path.join(self.scraper.download_dir, str(guild.id))
            os.makedirs(download_path, exist_ok=True)
            
            embed = discord.Embed(
                title="✅ Viral Content Automation Setup Complete",
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
                value="• Viral content discovery\n• Automated downloading\n• TikTok upload script generation\n• Performance tracking",
                inline=False
            )
            
            embed.add_field(
                name="🚀 Commands Available",
                value="`/search-viral-content` - Find viral content\n`/download-viral-content` - Download from URL\n`/generate-tiktok-script` - Create upload script",
                inline=False
            )
            
            embed.add_field(
                name="📁 Download Directory",
                value=download_path,
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Setup failed: {e}", ephemeral=True)
    
    @app_commands.command(name="content-library", description="View downloaded viral content library")
    async def content_library(self, interaction: discord.Interaction):
        """Display library of downloaded viral content"""
        await interaction.response.defer()
        
        try:
            async with aiosqlite.connect(self.scraper.db_path) as db:
                cursor = await db.execute('''
                    SELECT title, platform, engagement_score, download_date, uploaded_to_tiktok
                    FROM downloaded_content 
                    WHERE guild_id = ?
                    ORDER BY download_date DESC LIMIT 10
                ''', (interaction.guild.id,))
                
                content_list = await cursor.fetchall()
                
                if not content_list:
                    await interaction.followup.send("No content downloaded yet. Use `/search-viral-content` to get started!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📚 Viral Content Library",
                    color=0x9932cc,
                    timestamp=datetime.now(timezone.utc)
                )
                
                for i, (title, platform, engagement, date, uploaded) in enumerate(content_list, 1):
                    status = "✅ Uploaded" if uploaded else "📁 Ready"
                    embed.add_field(
                        name=f"{i}. {title[:50]}",
                        value=f"**Platform:** {platform}\n**Engagement:** {engagement}\n**Status:** {status}",
                        inline=True
                    )
                
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"Library access failed: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ViralContentAutomation(bot))