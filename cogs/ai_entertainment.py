import discord
from discord.ext import commands
from discord import app_commands
import openai
import random
import os
from datetime import datetime, timezone

class AIEntertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def get_ai_response(self, prompt: str, persona: str = None, user_context: str = None) -> str:
        """Get AI response with optional persona and context"""
        try:
            personas = {
                'wizard': 'You are Merlin, a wise ancient wizard. Speak mystically with magical wisdom.',
                'detective': 'You are Sherlock Holmes. Be analytical, observant, and methodical.',
                'comedian': 'You are a witty stand-up comedian. Make clever jokes and observations.',
                'therapist': 'You are a caring, professional therapist. Be supportive and insightful.',
                'coach': 'You are an energetic motivational coach. Be inspiring and action-oriented.'
            }
            
            messages = []
            if persona and persona in personas:
                messages.append({"role": "system", "content": personas[persona]})
            
            if user_context:
                prompt = f"Context: {user_context}\n\nRequest: {prompt}"
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.8
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI temporarily unavailable. Please try again later."

    @app_commands.command(name="ai-persona", description="Chat with different AI personalities")
    @app_commands.describe(persona="Choose AI personality", message="Your message to the AI")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Wizard", value="wizard"),
        app_commands.Choice(name="Detective", value="detective"),
        app_commands.Choice(name="Comedian", value="comedian"),
        app_commands.Choice(name="Therapist", value="therapist"),
        app_commands.Choice(name="Coach", value="coach")
    ])
    async def ai_persona(self, interaction: discord.Interaction, persona: str, message: str):
        """Chat with different AI personalities"""
        await interaction.response.defer()
        
        response = await self.get_ai_response(message, persona)
        
        persona_emojis = {
            'wizard': '🧙‍♂️',
            'detective': '🕵️',
            'comedian': '😂',
            'therapist': '🤝',
            'coach': '💪'
        }
        
        embed = discord.Embed(
            title=f"{persona_emojis.get(persona, '🤖')} AI {persona.title()}",
            description=response,
            color=0x00ff88,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-story", description="Start an interactive story with AI")
    @app_commands.describe(genre="Story genre")
    @app_commands.choices(genre=[
        app_commands.Choice(name="Fantasy Adventure", value="fantasy"),
        app_commands.Choice(name="Sci-Fi Mystery", value="scifi"),
        app_commands.Choice(name="Detective Story", value="mystery"),
        app_commands.Choice(name="Epic Adventure", value="adventure"),
        app_commands.Choice(name="Horror Thriller", value="horror")
    ])
    async def ai_story(self, interaction: discord.Interaction, genre: str):
        """Start an interactive story with AI"""
        await interaction.response.defer()
        
        story_prompts = {
            "fantasy": "Create the beginning of a fantasy adventure story with magic, mythical creatures, and an epic quest. End with a choice for the reader.",
            "scifi": "Begin a sci-fi mystery on a space station or alien planet. Include technology and unknown phenomena. End with a decision point.",
            "mystery": "Start a detective mystery with clues and suspects. Create atmosphere and intrigue. End with options for investigation.",
            "adventure": "Create an exciting adventure story with danger and exploration. End with a crucial choice.",
            "horror": "Begin a thrilling horror story with suspense and mystery. Keep it spooky but not too graphic. End with options."
        }
        
        story = await self.get_ai_response(story_prompts.get(genre, "Start an exciting interactive story."))
        
        embed = discord.Embed(
            title=f"📖 {genre.title()} Story",
            description=story,
            color=0xff6b35,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Reply to continue the story!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-roast", description="Get a friendly AI roast")
    @app_commands.describe(target="User to roast (optional)")
    async def ai_roast(self, interaction: discord.Interaction, target: discord.Member = None):
        """Get a friendly AI roast"""
        await interaction.response.defer()
        
        if target is None:
            target = interaction.user
        
        roast_prompt = f"Give a playful, witty roast about someone named {target.display_name}. Keep it friendly and humorous, not mean or offensive. Be creative and clever."
        roast = await self.get_ai_response(roast_prompt, "comedian")
        
        embed = discord.Embed(
            title=f"🔥 AI Roast for {target.display_name}",
            description=roast,
            color=0xff4757,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="All in good fun!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-advice", description="Get personalized advice from AI therapist")
    @app_commands.describe(situation="Describe your situation")
    async def ai_advice(self, interaction: discord.Interaction, situation: str):
        """Get personalized advice from AI therapist"""
        await interaction.response.defer()
        
        advice_prompt = f"Someone is dealing with this situation: {situation}. Provide thoughtful, supportive advice as a professional therapist would. Be empathetic and practical."
        advice = await self.get_ai_response(advice_prompt, "therapist")
        
        embed = discord.Embed(
            title="🤝 AI Therapist Advice",
            description=advice,
            color=0x2ed573,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Remember: This is AI advice, not professional therapy")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-motivate", description="Get personalized motivation")
    @app_commands.describe(goal="What you want to achieve (optional)")
    async def ai_motivate(self, interaction: discord.Interaction, goal: str = None):
        """Get personalized motivation"""
        await interaction.response.defer()
        
        if goal:
            prompt = f"Give energetic, inspiring motivation for someone working toward this goal: {goal}. Be positive and actionable."
        else:
            prompt = "Give general motivation and inspiration. Be energetic, positive, and encouraging about pursuing dreams and overcoming challenges."
        
        motivation = await self.get_ai_response(prompt, "coach")
        
        embed = discord.Embed(
            title="💪 AI Motivation",
            description=motivation,
            color=0x2ed573,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="You've got this!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-create", description="Collaborate with AI on creative projects")
    @app_commands.describe(project_type="What to create", topic="Topic or theme")
    @app_commands.choices(project_type=[
        app_commands.Choice(name="Poem", value="poem"),
        app_commands.Choice(name="Song Lyrics", value="lyrics"),
        app_commands.Choice(name="Short Story", value="story"),
        app_commands.Choice(name="Business Idea", value="business"),
        app_commands.Choice(name="Creative Writing", value="creative")
    ])
    async def ai_create(self, interaction: discord.Interaction, project_type: str, topic: str):
        """Collaborate with AI on creative projects"""
        await interaction.response.defer()
        
        creation_prompts = {
            "poem": f"Write a creative, expressive poem about {topic}. Use vivid imagery and emotion.",
            "lyrics": f"Write song lyrics about {topic}. Include verses and a catchy chorus.",
            "story": f"Write a compelling short story about {topic}. Create interesting characters and plot.",
            "business": f"Create an innovative business idea related to {topic}. Include the concept, target market, and potential.",
            "creative": f"Write a piece of creative content about {topic}. Be imaginative and original."
        }
        
        creation = await self.get_ai_response(creation_prompts[project_type])
        
        project_emojis = {
            "poem": "📝",
            "lyrics": "🎵",
            "story": "📖",
            "business": "💡",
            "creative": "🎨"
        }
        
        embed = discord.Embed(
            title=f"{project_emojis.get(project_type, '🎨')} AI {project_type.title()}: {topic}",
            description=creation[:2000] if len(creation) > 2000 else creation,
            color=0xf39c12,
            timestamp=datetime.now(timezone.utc)
        )
        
        if len(creation) > 2000:
            embed.set_footer(text="Content truncated - full version too long for Discord")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-debate", description="Start a debate with AI taking opposing viewpoints")
    @app_commands.describe(topic="Debate topic")
    async def ai_debate(self, interaction: discord.Interaction, topic: str):
        """Start a debate with AI taking opposing viewpoints"""
        await interaction.response.defer()
        
        debate_prompt = f"Present a balanced debate on this topic: {topic}. Show strong arguments for both sides. Be thoughtful and analytical."
        debate = await self.get_ai_response(debate_prompt, "detective")
        
        embed = discord.Embed(
            title=f"⚖️ AI Debate: {topic}",
            description=debate,
            color=0x7b68ee,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="What's your stance on this topic?")
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIEntertainment(bot))