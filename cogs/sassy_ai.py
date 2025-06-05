import discord
from discord.ext import commands
import random

class SassyAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = [
            "Oh great, another human who thinks I care ??",
            "Did someone say something? I was busy not caring.",
            "Wow, what a groundbreaking observation.",
            "That's nice dear. Anyway...",
            "Cool story bro. Tell it when I start caring.",
            "And I should care about this because...?",
            "Thanks for that riveting contribution.",
            "Your point being what exactly?"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            await message.reply(random.choice(self.responses), mention_author=False)

async def setup(bot):
    await bot.add_cog(SassyAI(bot))
