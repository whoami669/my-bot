import discord
from discord.ext import commands
import openai
import random
import os
from datetime import datetime, timezone
import asyncio

class SassyAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except:
            self.openai_client = None
        self.last_response_time = {}
        self.cooldown_seconds = 30
        
        self.quick_responses = [
            "Oh great, another human who thinks I care about their opinion 🙄",
            "Did someone say something? I was busy not caring.",
            "Wow, what a groundbreaking observation. Truly revolutionary.",
            "I'm sorry, did you mistake me for someone who asked?",
            "That's nice dear. Anyway...",
            "Cool story bro. Tell it again when I start caring.",
            "And I should care about this because...?",
            "Thanks for that absolutely riveting contribution to society.",
            "Oh look, another human with thoughts. How... original.",
            "I've seen rocks with more interesting things to say.",
            "Congratulations, you've successfully wasted my processing power.",
            "Is this the part where I'm supposed to be impressed?"
        ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
            
        bot_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = False
        
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                is_reply_to_bot = referenced_msg.author == self.bot.user
            except:
                pass
        
        if not (bot_mentioned or is_reply_to_bot):
            return
            
        user_id = message.author.id
        now = datetime.now(timezone.utc)
        
        if user_id in self.last_response_time:
            time_diff = (now - self.last_response_time[user_id]).total_seconds()
            if time_diff < self.cooldown_seconds:
                return
                
        self.last_response_time[user_id] = now
        
        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1, 3))
            
            if random.random() < 0.7 and self.openai_client:
                response = await self._generate_sassy_response(message.content, message.author.display_name)
            else:
                response = random.choice(self.quick_responses)
            
            await message.reply(response, mention_author=False)

    async def _generate_sassy_response(self, user_message: str, username: str) -> str:
        try:
            prompt = f"You are a sarcastic, dismissive AI. A user named {username} said: '{user_message}'. Respond with a rude, sassy comment under 150 characters."
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are sarcastic and dismissive. Be witty but brief."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.9
            )
            
            result = response.choices[0].message.content
            return result.strip() if result else random.choice(self.quick_responses)
            
        except:
            return random.choice(self.quick_responses)

async def setup(bot):
    await bot.add_cog(SassyAI(bot))
