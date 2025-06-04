import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiosqlite
from datetime import datetime, timedelta
import random

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(time="Time in minutes", message="Reminder message")
    async def remind(self, interaction: discord.Interaction, time: int, message: str):
        if time <= 0 or time > 10080:  # Max 7 days
            await interaction.response.send_message("Time must be between 1 minute and 7 days (10080 minutes)!", ephemeral=True)
            return
            
        remind_time = datetime.now() + timedelta(minutes=time)
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (interaction.user.id, interaction.guild.id, interaction.channel.id, message, remind_time))
            await db.commit()
        
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you in {time} minutes: {message}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(question="Poll question", options="Options separated by commas (max 10)")
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        
        if len(option_list) < 2:
            await interaction.response.send_message("You need at least 2 options!", ephemeral=True)
            return
            
        if len(option_list) > 10:
            await interaction.response.send_message("Maximum 10 options allowed!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue()
        )
        
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        poll_text = ""
        for i, option in enumerate(option_list):
            poll_text += f"{reactions[i]} {option}\n"
        
        embed.add_field(name="Options", value=poll_text, inline=False)
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(option_list)):
            await message.add_reaction(reactions[i])

    @app_commands.command(name="choose", description="Choose randomly from options")
    @app_commands.describe(options="Options separated by commas")
    async def choose(self, interaction: discord.Interaction, options: str):
        option_list = [opt.strip() for opt in options.split(',')]
        
        if len(option_list) < 2:
            await interaction.response.send_message("You need at least 2 options!", ephemeral=True)
            return
        
        choice = random.choice(option_list)
        
        embed = discord.Embed(
            title="🎲 Random Choice",
            description=f"I choose: **{choice}**",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt", "Yes definitely",
            "You may rely on it", "As I see it, yes", "Most likely", "Outlook good",
            "Yes", "Signs point to yes", "Reply hazy, try again", "Ask again later",
            "Better not tell you now", "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "My sources say no",
            "Outlook not so good", "Very doubtful"
        ]
        
        response = random.choice(responses)
        
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.dark_blue()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=response, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="Roll dice")
    @app_commands.describe(sides="Number of sides (default 6)", count="Number of dice (default 1)")
    async def dice(self, interaction: discord.Interaction, sides: int = 6, count: int = 1):
        if sides < 2 or sides > 100:
            await interaction.response.send_message("Sides must be between 2 and 100!", ephemeral=True)
            return
            
        if count < 1 or count > 20:
            await interaction.response.send_message("Count must be between 1 and 20!", ephemeral=True)
            return
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=discord.Color.green()
        )
        
        if count == 1:
            embed.description = f"You rolled a **{rolls[0]}**"
        else:
            embed.add_field(name="Rolls", value=" + ".join(map(str, rolls)), inline=False)
            embed.add_field(name="Total", value=str(total), inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="flip", description="Flip a coin")
    async def flip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🔄"
        
        embed = discord.Embed(
            title=f"{emoji} Coin Flip",
            description=f"Result: **{result}**",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="say", description="Make the bot say something")
    @app_commands.describe(message="Message to say", channel="Channel to send to")
    @app_commands.default_permissions(manage_messages=True)
    async def say(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        
        try:
            await target_channel.send(message)
            await interaction.response.send_message(f"Message sent to {target_channel.mention}!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send messages in that channel!", ephemeral=True)

    @app_commands.command(name="embed", description="Create an embed message")
    @app_commands.describe(title="Embed title", description="Embed description", color="Hex color code")
    @app_commands.default_permissions(manage_messages=True)
    async def embed_create(self, interaction: discord.Interaction, title: str, description: str, color: str = None):
        try:
            if color:
                if color.startswith('#'):
                    color = color[1:]
                embed_color = discord.Color(int(color, 16))
            else:
                embed_color = discord.Color.blue()
        except ValueError:
            await interaction.response.send_message("Invalid color code! Use hex format like #FF0000", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )
        embed.set_footer(text=f"Created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="membercount", description="Get server member count")
    async def membercount(self, interaction: discord.Interaction):
        guild = interaction.guild
        total = guild.member_count
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bots = sum(1 for member in guild.members if member.bot)
        humans = total - bots
        
        embed = discord.Embed(
            title="👥 Member Count",
            color=discord.Color.blue()
        )
        embed.add_field(name="Total Members", value=total, inline=True)
        embed.add_field(name="Humans", value=humans, inline=True)
        embed.add_field(name="Bots", value=bots, inline=True)
        embed.add_field(name="Online", value=online, inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))