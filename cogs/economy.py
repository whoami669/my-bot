import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime, timedelta
import aiosqlite

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_balance(self, guild_id, user_id):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

    async def update_balance(self, guild_id, user_id, amount):
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_daily, last_work, last_crime)
                VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0) + ?, 
                        COALESCE((SELECT last_daily FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT last_work FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT last_crime FROM economy WHERE guild_id = ? AND user_id = ?), 0))
            ''', (guild_id, user_id, guild_id, user_id, amount, guild_id, user_id, guild_id, user_id, guild_id, user_id))
            await db.commit()

    @app_commands.command(name="balance", description="Check your or someone's balance")
    @app_commands.describe(user="User to check balance for")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        balance = await self.get_balance(interaction.guild.id, target.id)
        
        embed = discord.Embed(
            title="💰 Balance",
            description=f"{target.display_name}: **${balance:,}**",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT last_daily, daily_streak FROM economy WHERE guild_id = ? AND user_id = ?',
                (interaction.guild.id, interaction.user.id)
            ) as cursor:
                result = await cursor.fetchone()
                
            last_daily = result[0] if result and result[0] else 0
            streak = result[1] if result and result[1] else 0
            
            now = datetime.now().timestamp()
            day_seconds = 86400  # 24 hours
            
            if now - last_daily < day_seconds:
                next_daily = last_daily + day_seconds
                wait_time = int(next_daily - now)
                hours, remainder = divmod(wait_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed = discord.Embed(
                    title="⏰ Daily Cooldown",
                    description=f"You can claim your daily reward in {hours}h {minutes}m {seconds}s",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if streak continues (claimed within 48 hours)
            if now - last_daily <= day_seconds * 2:
                streak += 1
            else:
                streak = 1
            
            # Calculate reward based on streak
            base_reward = 100
            streak_bonus = min(streak * 10, 500)  # Max 500 bonus
            total_reward = base_reward + streak_bonus
            
            await self.update_balance(interaction.guild.id, interaction.user.id, total_reward)
            
            await db.execute('''
                INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_daily, daily_streak, last_work, last_crime)
                VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        ?, ?, 
                        COALESCE((SELECT last_work FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT last_crime FROM economy WHERE guild_id = ? AND user_id = ?), 0))
            ''', (interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id,
                  now, streak, interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id))
            await db.commit()
        
        embed = discord.Embed(
            title="💰 Daily Reward Claimed!",
            description=f"You received **${total_reward:,}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Streak", value=f"{streak} days", inline=True)
        embed.add_field(name="Bonus", value=f"${streak_bonus:,}", inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work to earn money")
    async def work(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT last_work FROM economy WHERE guild_id = ? AND user_id = ?',
                (interaction.guild.id, interaction.user.id)
            ) as cursor:
                result = await cursor.fetchone()
                
            last_work = result[0] if result and result[0] else 0
            now = datetime.now().timestamp()
            cooldown = 3600  # 1 hour
            
            if now - last_work < cooldown:
                wait_time = int(last_work + cooldown - now)
                hours, remainder = divmod(wait_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed = discord.Embed(
                    title="⏰ Work Cooldown",
                    description=f"You can work again in {hours}h {minutes}m {seconds}s",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            jobs = [
                ("Developer", 150, 300),
                ("Teacher", 100, 200),
                ("Chef", 120, 250),
                ("Artist", 80, 180),
                ("Writer", 90, 220),
                ("Musician", 110, 240),
                ("Doctor", 200, 400),
                ("Engineer", 180, 350)
            ]
            
            job, min_pay, max_pay = random.choice(jobs)
            earned = random.randint(min_pay, max_pay)
            
            await self.update_balance(interaction.guild.id, interaction.user.id, earned)
            
            await db.execute('''
                INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_work, last_daily, daily_streak, last_crime)
                VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        ?, 
                        COALESCE((SELECT last_daily FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT daily_streak FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT last_crime FROM economy WHERE guild_id = ? AND user_id = ?), 0))
            ''', (interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id,
                  now, interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id,
                  interaction.guild.id, interaction.user.id))
            await db.commit()
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"You worked as a **{job}** and earned **${earned:,}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="crime", description="Commit a crime for money (risky)")
    async def crime(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT last_crime FROM economy WHERE guild_id = ? AND user_id = ?',
                (interaction.guild.id, interaction.user.id)
            ) as cursor:
                result = await cursor.fetchone()
                
            last_crime = result[0] if result and result[0] else 0
            now = datetime.now().timestamp()
            cooldown = 7200  # 2 hours
            
            if now - last_crime < cooldown:
                wait_time = int(last_crime + cooldown - now)
                hours, remainder = divmod(wait_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                embed = discord.Embed(
                    title="⏰ Crime Cooldown",
                    description=f"You can commit a crime again in {hours}h {minutes}m {seconds}s",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            crimes = [
                ("Shoplifting", 200, 500, 0.7),
                ("Pickpocketing", 150, 400, 0.6),
                ("Bank Robbery", 500, 1000, 0.3),
                ("Hacking", 300, 800, 0.5),
                ("Art Theft", 400, 900, 0.4)
            ]
            
            crime, min_reward, max_reward, success_rate = random.choice(crimes)
            success = random.random() < success_rate
            
            if success:
                earned = random.randint(min_reward, max_reward)
                await self.update_balance(interaction.guild.id, interaction.user.id, earned)
                
                embed = discord.Embed(
                    title="🎯 Crime Successful!",
                    description=f"You successfully committed **{crime}** and earned **${earned:,}**",
                    color=discord.Color.green()
                )
            else:
                fine = random.randint(100, 300)
                current_balance = await self.get_balance(interaction.guild.id, interaction.user.id)
                fine = min(fine, current_balance)  # Can't lose more than you have
                
                if fine > 0:
                    await self.update_balance(interaction.guild.id, interaction.user.id, -fine)
                
                embed = discord.Embed(
                    title="🚨 Crime Failed!",
                    description=f"You were caught attempting **{crime}** and fined **${fine:,}**",
                    color=discord.Color.red()
                )
            
            await db.execute('''
                INSERT OR REPLACE INTO economy (guild_id, user_id, balance, last_crime, last_daily, daily_streak, last_work)
                VALUES (?, ?, COALESCE((SELECT balance FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        ?, 
                        COALESCE((SELECT last_daily FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT daily_streak FROM economy WHERE guild_id = ? AND user_id = ?), 0),
                        COALESCE((SELECT last_work FROM economy WHERE guild_id = ? AND user_id = ?), 0))
            ''', (interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id,
                  now, interaction.guild.id, interaction.user.id, interaction.guild.id, interaction.user.id,
                  interaction.guild.id, interaction.user.id))
            await db.commit()
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the server's richest members")
    async def leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT user_id, balance FROM economy WHERE guild_id = ? ORDER BY balance DESC LIMIT 10',
                (interaction.guild.id,)
            ) as cursor:
                results = await cursor.fetchall()
        
        if not results:
            embed = discord.Embed(
                title="💰 Economy Leaderboard",
                description="No economy data found for this server",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="💰 Economy Leaderboard",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        description = ""
        
        for i, (user_id, balance) in enumerate(results):
            user = self.bot.get_user(user_id)
            if user:
                medal = medals[i] if i < 3 else f"{i+1}."
                description += f"{medal} **{user.display_name}** - ${balance:,}\n"
        
        embed.description = description
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))