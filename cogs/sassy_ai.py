import discord
from discord.ext import commands
import random

class SassyAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.responses = [
            "Oh great, another human who thinks I care 🙄",
            "Did someone say something? I was busy not caring.",
            "Wow, what a groundbreaking observation.",
            "Cool story bro. Tell it when I start caring.",
            "That's nice dear. Anyway...",
            "And I should care about this because...?"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user in message.mentions:
            await message.reply(random.choice(self.responses), mention_author=False)

async def setup(bot):
    await bot.add_cog(SassyAI(bot))
