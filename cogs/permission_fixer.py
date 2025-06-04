import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class PermissionFixer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fix-bot-permissions", description="Enable bot commands for all members in all channels")
    @app_commands.default_permissions(administrator=True)
    async def fix_bot_permissions(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔧 Fixing Bot Permissions",
            description="Starting to configure all channels for bot access...",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        
        guild = interaction.guild
        bot_member = guild.me
        
        success_count = 0
        error_count = 0
        total_channels = len(guild.channels)
        
        # Find or create Members role
        members_role = discord.utils.get(guild.roles, name="Members")
        if not members_role:
            try:
                members_role = await guild.create_role(
                    name="Members",
                    color=discord.Color.blue(),
                    reason="Created by bot for permission management"
                )
            except discord.Forbidden:
                await interaction.followup.send("❌ Cannot create Members role - insufficient permissions")
                return
        
        # Process all channels
        for channel in guild.channels:
            try:
                # Set bot permissions
                await channel.set_permissions(
                    bot_member,
                    view_channel=True,
                    send_messages=True,
                    use_application_commands=True,
                    embed_links=True,
                    read_message_history=True,
                    connect=True if isinstance(channel, discord.VoiceChannel) else None,
                    speak=True if isinstance(channel, discord.VoiceChannel) else None,
                    reason="Bot permission fix"
                )
                
                # Set @everyone permissions for bot commands
                await channel.set_permissions(
                    guild.default_role,
                    use_application_commands=True,
                    reason="Enable bot commands for everyone"
                )
                
                # Set Members role permissions
                await channel.set_permissions(
                    members_role,
                    view_channel=True,
                    send_messages=True,
                    use_application_commands=True,
                    connect=True if isinstance(channel, discord.VoiceChannel) else None,
                    speak=True if isinstance(channel, discord.VoiceChannel) else None,
                    reason="Members role permissions"
                )
                
                success_count += 1
                
            except discord.Forbidden:
                error_count += 1
            except Exception:
                error_count += 1
        
        # Final result
        result_embed = discord.Embed(
            title="✅ Bot Permission Fix Complete",
            color=discord.Color.green()
        )
        result_embed.add_field(name="Channels Fixed", value=success_count, inline=True)
        result_embed.add_field(name="Errors", value=error_count, inline=True)
        result_embed.add_field(name="Total Channels", value=total_channels, inline=True)
        result_embed.add_field(
            name="Members Role", 
            value=f"{'Created' if not discord.utils.get(guild.roles, name='Members') else 'Updated'}: {members_role.mention}",
            inline=False
        )
        
        await interaction.followup.send(embed=result_embed)

    @app_commands.command(name="assign-members-role", description="Give Members role to all users in the server")
    @app_commands.default_permissions(administrator=True)
    async def assign_members_role(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        members_role = discord.utils.get(guild.roles, name="Members")
        
        if not members_role:
            await interaction.followup.send("❌ Members role not found. Run `/fix-bot-permissions` first.")
            return
        
        success_count = 0
        error_count = 0
        already_has = 0
        
        embed = discord.Embed(
            title="👥 Assigning Members Role",
            description=f"Adding {members_role.mention} to all users...",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        
        for member in guild.members:
            if member.bot:
                continue
                
            try:
                if members_role in member.roles:
                    already_has += 1
                else:
                    await member.add_roles(members_role, reason="Auto-assign Members role")
                    success_count += 1
                    
            except discord.Forbidden:
                error_count += 1
            except Exception:
                error_count += 1
        
        result_embed = discord.Embed(
            title="✅ Members Role Assignment Complete",
            color=discord.Color.green()
        )
        result_embed.add_field(name="Assigned", value=success_count, inline=True)
        result_embed.add_field(name="Already Had Role", value=already_has, inline=True)
        result_embed.add_field(name="Errors", value=error_count, inline=True)
        
        await interaction.followup.send(embed=result_embed)

    @app_commands.command(name="unlock-voice-channels", description="Unlock all voice channels for Members role")
    @app_commands.default_permissions(administrator=True)
    async def unlock_voice_channels(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        members_role = discord.utils.get(guild.roles, name="Members")
        
        if not members_role:
            await interaction.followup.send("❌ Members role not found. Run `/fix-bot-permissions` first.")
            return
        
        success_count = 0
        error_count = 0
        
        voice_channels = [ch for ch in guild.channels if isinstance(ch, discord.VoiceChannel)]
        
        embed = discord.Embed(
            title="🔊 Unlocking Voice Channels",
            description=f"Configuring {len(voice_channels)} voice channels...",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        
        for channel in voice_channels:
            try:
                await channel.set_permissions(
                    members_role,
                    view_channel=True,
                    connect=True,
                    speak=True,
                    use_voice_activation=True,
                    reason="Unlock voice channel for members"
                )
                success_count += 1
                
            except discord.Forbidden:
                error_count += 1
            except Exception:
                error_count += 1
        
        result_embed = discord.Embed(
            title="✅ Voice Channels Unlocked",
            color=discord.Color.green()
        )
        result_embed.add_field(name="Unlocked", value=success_count, inline=True)
        result_embed.add_field(name="Errors", value=error_count, inline=True)
        result_embed.add_field(name="Total Voice Channels", value=len(voice_channels), inline=True)
        
        await interaction.followup.send(embed=result_embed)

    @app_commands.command(name="server-setup-complete", description="Run all setup commands in sequence")
    @app_commands.default_permissions(administrator=True)
    async def server_setup_complete(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🚀 Complete Server Setup",
            description="Running all setup commands in sequence...",
            color=discord.Color.gold()
        )
        await interaction.followup.send(embed=embed)
        
        # Step 1: Fix bot permissions
        await self.fix_bot_permissions(interaction)
        await asyncio.sleep(2)
        
        # Step 2: Assign members role
        await self.assign_members_role(interaction)
        await asyncio.sleep(2)
        
        # Step 3: Unlock voice channels
        await self.unlock_voice_channels(interaction)
        
        final_embed = discord.Embed(
            title="🎉 Server Setup Complete!",
            description="Your server is now fully configured:",
            color=discord.Color.green()
        )
        final_embed.add_field(
            name="✅ Completed Tasks",
            value="• Bot permissions fixed in all channels\n• Members role created and assigned\n• Voice channels unlocked\n• Bot commands enabled for everyone",
            inline=False
        )
        
        await interaction.followup.send(embed=final_embed)

async def setup(bot):
    await bot.add_cog(PermissionFixer(bot))