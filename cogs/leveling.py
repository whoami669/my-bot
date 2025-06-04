import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import math
import random
import asyncio

class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def calculate_level(self, xp):
        return int(math.sqrt(xp / 100))

    def calculate_xp_for_level(self, level):
        return (level ** 2) * 100

    async def add_xp(self, guild_id, user_id, amount):
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get current XP and level
            async with db.execute(
                'SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            ) as cursor:
                result = await cursor.fetchone()
                
            current_xp = result[0] if result else 0
            current_level = result[1] if result else 0
            
            new_xp = current_xp + amount
            new_level = self.calculate_level(new_xp)
            
            # Update database
            await db.execute('''
                INSERT OR REPLACE INTO levels (guild_id, user_id, xp, level)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, new_xp, new_level))
            await db.commit()
            
            return current_level, new_level, new_xp

    @app_commands.command(name="rank", description="Check your or someone's rank and level")
    @app_commands.describe(user="User to check rank for")
    async def rank(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        async with aiosqlite.connect('ultrabot.db') as db:
            # Get user's stats
            async with db.execute(
                'SELECT xp, level FROM levels WHERE guild_id = ? AND user_id = ?',
                (interaction.guild.id, target.id)
            ) as cursor:
                result = await cursor.fetchone()
                
            if not result:
                embed = discord.Embed(
                    title="📊 Rank",
                    description=f"{target.display_name} hasn't earned any XP yet!",
                    color=discord.Color.gray()
                )
                await interaction.response.send_message(embed=embed)
                return
            
            xp, level = result
            
            # Get user's rank
            async with db.execute(
                'SELECT COUNT(*) + 1 FROM levels WHERE guild_id = ? AND xp > ?',
                (interaction.guild.id, xp)
            ) as cursor:
                rank = (await cursor.fetchone())[0]
            
            # Calculate XP for current and next level
            current_level_xp = self.calculate_xp_for_level(level)
            next_level_xp = self.calculate_xp_for_level(level + 1)
            progress_xp = xp - current_level_xp
            needed_xp = next_level_xp - current_level_xp
            
            # Create progress bar
            progress = progress_xp / needed_xp
            bar_length = 20
            filled = int(progress * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            embed = discord.Embed(
                title="📊 Rank Card",
                color=target.color if target.color != discord.Color.default() else discord.Color.blue()
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="User", value=target.display_name, inline=True)
            embed.add_field(name="Rank", value=f"#{rank}", inline=True)
            embed.add_field(name="Level", value=level, inline=True)
            embed.add_field(name="XP", value=f"{xp:,}", inline=True)
            embed.add_field(name="Progress", value=f"{progress_xp}/{needed_xp}", inline=True)
            embed.add_field(name="Progress Bar", value=f"`{bar}` {progress:.1%}", inline=False)
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard-xp", description="View the XP leaderboard")
    async def leaderboard_xp(self, interaction: discord.Interaction):
        async with aiosqlite.connect('ultrabot.db') as db:
            async with db.execute(
                'SELECT user_id, xp, level FROM levels WHERE guild_id = ? ORDER BY xp DESC LIMIT 10',
                (interaction.guild.id,)
            ) as cursor:
                results = await cursor.fetchall()
        
        if not results:
            embed = discord.Embed(
                title="📊 XP Leaderboard",
                description="No XP data found for this server",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title="📊 XP Leaderboard",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        description = ""
        
        for i, (user_id, xp, level) in enumerate(results):
            user = self.bot.get_user(user_id)
            if user:
                medal = medals[i] if i < 3 else f"{i+1}."
                description += f"{medal} **{user.display_name}** - Level {level} ({xp:,} XP)\n"
        
        embed.description = description
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="give-xp", description="Give XP to a user (Admin only)")
    @app_commands.describe(user="User to give XP to", amount="Amount of XP to give")
    @app_commands.default_permissions(administrator=True)
    async def give_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0 or amount > 10000:
            await interaction.response.send_message("Amount must be between 1 and 10,000!", ephemeral=True)
            return
        
        old_level, new_level, new_xp = await self.add_xp(interaction.guild.id, user.id, amount)
        
        embed = discord.Embed(
            title="✨ XP Given",
            description=f"Gave {amount:,} XP to {user.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="New XP", value=f"{new_xp:,}", inline=True)
        embed.add_field(name="New Level", value=new_level, inline=True)
        
        if new_level > old_level:
            embed.add_field(name="Level Up!", value=f"Level {old_level} → {new_level}", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset-levels", description="Reset all levels in the server (Admin only)")
    @app_commands.default_permissions(administrator=True)
    async def reset_levels(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚠️ Confirm Reset",
            description="Are you sure you want to reset ALL levels and XP in this server? This cannot be undone!",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        message = await interaction.original_response()
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30)
            
            if str(reaction.emoji) == "✅":
                async with aiosqlite.connect('ultrabot.db') as db:
                    await db.execute('DELETE FROM levels WHERE guild_id = ?', (interaction.guild.id,))
                    await db.commit()
                
                success_embed = discord.Embed(
                    title="✅ Levels Reset",
                    description="All levels and XP have been reset for this server.",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=success_embed, ephemeral=True)
            else:
                cancel_embed = discord.Embed(
                    title="❌ Reset Cancelled",
                    description="Level reset has been cancelled.",
                    color=discord.Color.gray()
                )
                await interaction.followup.send(embed=cancel_embed, ephemeral=True)
                
        except:
            timeout_embed = discord.Embed(
                title="⏰ Timeout",
                description="Reset confirmation timed out.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=timeout_embed, ephemeral=True)

    # Automatic XP gain disabled to prevent unwanted messages

async def setup(bot):
    await bot.add_cog(Leveling(bot))