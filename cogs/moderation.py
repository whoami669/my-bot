import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason for kicking")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot kick someone with equal or higher role!", ephemeral=True)
            return
            
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="🦶 Member Kicked",
                description=f"{member.mention} has been kicked",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick this member!", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason for banning", delete_messages="Days of messages to delete (0-7)")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_messages: int = 0):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot ban someone with equal or higher role!", ephemeral=True)
            return
            
        if delete_messages < 0 or delete_messages > 7:
            await interaction.response.send_message("Delete messages days must be between 0 and 7!", ephemeral=True)
            return
            
        try:
            await member.ban(reason=reason, delete_message_days=delete_messages)
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban this member!", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="ID of the user to unban", reason="Reason for unbanning")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        try:
            user_id_int = int(user_id)
            user = await self.bot.fetch_user(user_id_int)
            await interaction.guild.unban(user, reason=reason)
            
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{user.mention} has been unbanned",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        except ValueError:
            await interaction.response.send_message("Invalid user ID!", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("User not found or not banned!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to unban users!", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="Member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot timeout someone with equal or higher role!", ephemeral=True)
            return
            
        if duration <= 0 or duration > 40320:  # Max 28 days
            await interaction.response.send_message("Duration must be between 1 minute and 28 days (40320 minutes)!", ephemeral=True)
            return
            
        try:
            until = datetime.utcnow() + timedelta(minutes=duration)
            await member.timeout(until, reason=reason)
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"{member.mention} has been timed out for {duration} minutes",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Until", value=f"<t:{int(until.timestamp())}:R>", inline=True)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout this member!", ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="Member to remove timeout from", reason="Reason for removing timeout")
    @app_commands.default_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            await member.timeout(None, reason=reason)
            
            embed = discord.Embed(
                title="✅ Timeout Removed",
                description=f"Timeout removed from {member.mention}",
                color=discord.Color.green()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to remove timeout from this member!", ephemeral=True)

    @app_commands.command(name="clear", description="Clear messages from the channel")
    @app_commands.describe(amount="Number of messages to delete (1-100)", user="Only delete messages from this user")
    @app_commands.default_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):
        if amount <= 0 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        def check(message):
            if user:
                return message.author == user
            return True
            
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"Deleted {len(deleted)} messages",
                color=discord.Color.green()
            )
            if user:
                embed.add_field(name="User", value=user.mention, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to delete messages!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))