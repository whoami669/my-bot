import discord
from discord.ext import commands
from discord import app_commands
import openai
import os
import asyncio
import aiosqlite
from typing import Dict, List

class AIConversationManager:
    def __init__(self, max_context_length: int = 8):
        self.conversations: Dict[str, List[Dict]] = {}
        self.max_context_length = max_context_length

    def get_conversation(self, user_id: int, channel_id: int) -> List[Dict]:
        key = f"{user_id}_{channel_id}"
        return self.conversations.get(key, [])

    def add_message(self, user_id: int, channel_id: int, role: str, content: str):
        key = f"{user_id}_{channel_id}"
        if key not in self.conversations:
            self.conversations[key] = []
        
        self.conversations[key].append({"role": role, "content": content})
        
        if len(self.conversations[key]) > self.max_context_length:
            self.conversations[key] = self.conversations[key][-self.max_context_length:]

    def clear_conversation(self, user_id: int, channel_id: int):
        key = f"{user_id}_{channel_id}"
        if key in self.conversations:
            del self.conversations[key]

class AIFeatures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_manager = AIConversationManager()
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    @app_commands.command(name="ai", description="Chat with AI assistant")
    @app_commands.describe(
        prompt="Your message to the AI",
        model="AI model to use",
        system="System prompt for AI behavior",
        remember="Whether to remember conversation context"
    )
    async def ai(self, interaction: discord.Interaction, prompt: str, 
                 model: str = "gpt-4o", system: str = None, remember: bool = True):
        
        await interaction.response.defer()
        
        try:
            if remember:
                conversation = self.conversation_manager.get_conversation(
                    interaction.user.id, interaction.channel.id
                )
            else:
                conversation = []

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            
            messages.extend(conversation)
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content

            if remember:
                self.conversation_manager.add_message(
                    interaction.user.id, interaction.channel.id, "user", prompt
                )
                self.conversation_manager.add_message(
                    interaction.user.id, interaction.channel.id, "assistant", ai_response
                )

            if len(ai_response) > 2000:
                chunks = [ai_response[i:i+2000] for i in range(0, len(ai_response), 2000)]
                await interaction.followup.send(chunks[0])
                for chunk in chunks[1:]:
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(ai_response)

        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")

    @app_commands.command(name="clear-conversation", description="Clear AI conversation memory")
    async def clear_conversation(self, interaction: discord.Interaction):
        self.conversation_manager.clear_conversation(interaction.user.id, interaction.channel.id)
        await interaction.response.send_message("Conversation memory cleared!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIFeatures(bot))