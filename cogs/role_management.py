import discord
from discord.ext import commands
from discord import app_commands

class RoleManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="role-add", description="Add a role to a user")
    @app_commands.describe(user="User to give the role to", role="Role to add")
    @app_commands.default_permissions(manage_roles=True)
    async def role_add(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot assign a role equal to or higher than your own!", ephemeral=True)
            return
            
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot assign a role equal to or higher than my own!", ephemeral=True)
            return
            
        if role in user.roles:
            await interaction.response.send_message(f"{user.mention} already has the {role.mention} role!", ephemeral=True)
            return
            
        try:
            await user.add_roles(role, reason=f"Role added by {interaction.user}")
            embed = discord.Embed(
                title="✅ Role Added",
                description=f"Added {role.mention} to {user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage this role!", ephemeral=True)

    @app_commands.command(name="role-remove", description="Remove a role from a user")
    @app_commands.describe(user="User to remove the role from", role="Role to remove")
    @app_commands.default_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot remove a role equal to or higher than your own!", ephemeral=True)
            return
            
        if role not in user.roles:
            await interaction.response.send_message(f"{user.mention} doesn't have the {role.mention} role!", ephemeral=True)
            return
            
        try:
            await user.remove_roles(role, reason=f"Role removed by {interaction.user}")
            embed = discord.Embed(
                title="✅ Role Removed",
                description=f"Removed {role.mention} from {user.mention}",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to manage this role!", ephemeral=True)

    @app_commands.command(name="role-all", description="Add or remove a role from all members")
    @app_commands.describe(role="Role to add/remove", action="Whether to add or remove the role")
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    @app_commands.default_permissions(administrator=True)
    async def role_all(self, interaction: discord.Interaction, role: discord.Role, action: str):
        if role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            await interaction.response.send_message("You cannot manage a role equal to or higher than your own!", ephemeral=True)
            return
            
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot manage a role equal to or higher than my own!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success_count = 0
        error_count = 0
        total_members = len([m for m in interaction.guild.members if not m.bot])
        
        embed = discord.Embed(
            title="🔄 Processing Role Changes",
            description=f"{'Adding' if action == 'add' else 'Removing'} {role.mention} {'to' if action == 'add' else 'from'} all members...",
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)
        
        for member in interaction.guild.members:
            if member.bot:
                continue
                
            try:
                if action == "add" and role not in member.roles:
                    await member.add_roles(role, reason=f"Mass role assignment by {interaction.user}")
                    success_count += 1
                elif action == "remove" and role in member.roles:
                    await member.remove_roles(role, reason=f"Mass role removal by {interaction.user}")
                    success_count += 1
            except:
                error_count += 1
        
        result_embed = discord.Embed(
            title="✅ Role Operation Complete",
            color=discord.Color.green()
        )
        result_embed.add_field(name="Successful", value=success_count, inline=True)
        result_embed.add_field(name="Errors", value=error_count, inline=True)
        result_embed.add_field(name="Total Members", value=total_members, inline=True)
        
        await interaction.followup.send(embed=result_embed)

    @app_commands.command(name="role-info", description="Get information about a role")
    @app_commands.describe(role="Role to get information about")
    async def role_info(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(
            title=f"📋 Role Information: {role.name}",
            color=role.color if role.color != discord.Color.default() else discord.Color.blue()
        )
        
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Members", value=len(role.members), inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Position", value=role.position, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:R>", inline=True)
        
        if role.permissions.administrator:
            embed.add_field(name="⚠️ Administrator", value="This role has administrator permissions", inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="role-list", description="List all roles in the server")
    async def role_list(self, interaction: discord.Interaction):
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        
        embed = discord.Embed(
            title="📋 Server Roles",
            color=discord.Color.blue()
        )
        
        role_text = ""
        for role in roles:
            if role.name != "@everyone":
                member_count = len(role.members)
                role_text += f"{role.mention} - {member_count} members\n"
        
        if len(role_text) > 1024:
            role_text = role_text[:1020] + "..."
        
        embed.description = role_text
        embed.set_footer(text=f"Total roles: {len(roles)-1}")  # -1 to exclude @everyone
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))