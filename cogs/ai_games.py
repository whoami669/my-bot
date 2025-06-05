import discord
from discord.ext import commands
from discord import app_commands
import openai
import random
import os
from datetime import datetime, timezone

class AIGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.active_games = {}

    async def get_ai_response(self, prompt: str, system_prompt: str = None) -> str:
        """Get AI response for games"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=400,
                temperature=0.8
            )
            return response.choices[0].message.content or "AI response unavailable"
        except Exception as e:
            return f"AI temporarily unavailable. Please try again later."

    @app_commands.command(name="twenty-questions", description="Start a game of 20 Questions with AI")
    async def twenty_questions(self, interaction: discord.Interaction):
        """Start a game of 20 Questions with AI"""
        await interaction.response.defer()
        
        prompt = "Think of a random object, person, or concept for a game of 20 Questions. Don't reveal what it is yet. Just say you're ready to play and give a hint about the category (like 'animal', 'object', 'person', etc.)."
        response = await self.get_ai_response(prompt)
        
        # Store game state
        self.active_games[interaction.user.id] = {
            'type': '20questions',
            'questions_left': 20,
            'channel_id': interaction.channel.id if interaction.channel else 0
        }
        
        embed = discord.Embed(
            title="🎯 20 Questions Game Started!",
            description=f"{response}\n\n**Questions remaining: 20**\nAsk yes/no questions to guess what I'm thinking of!",
            color=0x9b59b6,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-riddle", description="Generate a riddle with AI")
    @app_commands.describe(difficulty="Riddle difficulty level")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Easy", value="easy"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="Hard", value="hard")
    ])
    async def ai_riddle(self, interaction: discord.Interaction, difficulty: str = "medium"):
        """Generate a riddle with AI"""
        await interaction.response.defer()
        
        difficulty_prompts = {
            "easy": "Create an easy riddle suitable for children. Include the answer at the end marked with 'Answer:'",
            "medium": "Create a medium difficulty riddle with clever wordplay. Include the answer at the end marked with 'Answer:'",
            "hard": "Create a challenging riddle with complex wordplay and metaphors. Include the answer at the end marked with 'Answer:'"
        }
        
        riddle_text = await self.get_ai_response(difficulty_prompts[difficulty])
        
        # Split riddle and answer
        if "Answer:" in riddle_text:
            riddle, answer = riddle_text.split("Answer:", 1)
            riddle = riddle.strip()
            answer = answer.strip()
        else:
            riddle = riddle_text
            answer = "Check the AI response above"
        
        view = RiddleView(answer)
        
        embed = discord.Embed(
            title=f"🧩 {difficulty.title()} Riddle",
            description=riddle,
            color=0x9b59b6,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="ai-wordgame", description="Play collaborative word games with AI")
    @app_commands.describe(game_type="Type of word game")
    @app_commands.choices(game_type=[
        app_commands.Choice(name="Story Building", value="story"),
        app_commands.Choice(name="Rhyme Time", value="rhyme"),
        app_commands.Choice(name="Word Association", value="association")
    ])
    async def ai_wordgame(self, interaction: discord.Interaction, game_type: str):
        """Play collaborative word games with AI"""
        await interaction.response.defer()
        
        game_prompts = {
            "story": "Start a collaborative story with just one sentence. Make it interesting and leave it open for the next person to continue.",
            "rhyme": "Start a rhyming game. Give a word and challenge someone to rhyme with it, then continue the pattern.",
            "association": "Start a word association game. Give a starting word and explain the rules."
        }
        
        response = await self.get_ai_response(game_prompts[game_type])
        
        self.active_games[interaction.user.id] = {
            'type': 'wordgame',
            'game_type': game_type,
            'channel_id': interaction.channel.id if interaction.channel else 0
        }
        
        game_emojis = {"story": "📚", "rhyme": "🎵", "association": "🔗"}
        
        embed = discord.Embed(
            title=f"{game_emojis.get(game_type, '🎮')} {game_type.title().replace('_', ' ')} Game",
            description=response,
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Reply to participate!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ai-trivia", description="Generate trivia questions with AI")
    @app_commands.describe(category="Trivia category")
    @app_commands.choices(category=[
        app_commands.Choice(name="General Knowledge", value="general"),
        app_commands.Choice(name="Science", value="science"),
        app_commands.Choice(name="Movies & TV", value="movies"),
        app_commands.Choice(name="Music", value="music"),
        app_commands.Choice(name="Sports", value="sports"),
        app_commands.Choice(name="History", value="history")
    ])
    async def ai_trivia(self, interaction: discord.Interaction, category: str = "general"):
        """Generate trivia questions with AI"""
        await interaction.response.defer()
        
        prompt = f"Create a {category} trivia question with 4 multiple choice answers (A, B, C, D). Format it clearly with the question, then the four options, then state which letter is correct and provide a brief explanation."
        
        trivia_content = await self.get_ai_response(prompt)
        
        # Try to extract the correct answer
        correct_answer = "A"  # Default fallback
        explanation = "Check the AI response for details"
        
        for line in trivia_content.split('\n'):
            if 'correct' in line.lower() or 'answer' in line.lower():
                if any(letter in line.upper() for letter in ['A)', 'B)', 'C)', 'D)']):
                    for letter in ['A', 'B', 'C', 'D']:
                        if f'{letter})' in line or f'({letter})' in line:
                            correct_answer = letter
                            explanation = line
                            break
        
        view = TriviaView(correct_answer, explanation)
        
        embed = discord.Embed(
            title=f"🧠 {category.title()} Trivia",
            description=trivia_content.split('\n\n')[0] if '\n\n' in trivia_content else trivia_content,
            color=0xf39c12,
            timestamp=datetime.now(timezone.utc)
        )
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="ai-mystery", description="Generate interactive mystery scenarios")
    @app_commands.describe(difficulty="Mystery complexity")
    @app_commands.choices(difficulty=[
        app_commands.Choice(name="Simple", value="simple"),
        app_commands.Choice(name="Complex", value="complex")
    ])
    async def ai_mystery(self, interaction: discord.Interaction, difficulty: str = "simple"):
        """Generate interactive mystery scenarios"""
        await interaction.response.defer()
        
        if difficulty == "simple":
            prompt = "Create a simple mystery scenario with clues. Present the mystery and ask what the player wants to investigate first."
        else:
            prompt = "Create a complex mystery with multiple suspects and red herrings. Present the scenario and initial clues."
        
        mystery = await self.get_ai_response(prompt)
        
        self.active_games[interaction.user.id] = {
            'type': 'mystery',
            'difficulty': difficulty,
            'channel_id': interaction.channel.id if interaction.channel else 0
        }
        
        embed = discord.Embed(
            title=f"🔍 {difficulty.title()} Mystery",
            description=mystery,
            color=0x8e44ad,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Reply with your investigation choices!")
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle responses to active games"""
        if message.author.bot or message.author.id not in self.active_games:
            return
        
        game = self.active_games[message.author.id]
        
        if game['channel_id'] != (message.channel.id if message.channel else 0):
            return
        
        if game['type'] == '20questions':
            await self._handle_20questions(message, game)
        elif game['type'] == 'wordgame':
            await self._handle_wordgame(message, game)
        elif game['type'] == 'mystery':
            await self._handle_mystery(message, game)

    async def _handle_20questions(self, message, game):
        """Handle 20 questions responses"""
        game['questions_left'] -= 1
        
        if game['questions_left'] <= 0:
            response = await self.get_ai_response(f"The player asked: '{message.content}'. They're out of questions! Reveal what you were thinking of and whether they won or lost.")
            del self.active_games[message.author.id]
        else:
            response = await self.get_ai_response(f"Player question: '{message.content}'. Answer with yes/no and maybe a helpful hint. Don't reveal the answer yet.")
        
        embed = discord.Embed(
            title="🎯 20 Questions",
            description=f"{response}\n\n**Questions remaining: {game['questions_left']}**",
            color=0x9b59b6
        )
        await message.reply(embed=embed)

    async def _handle_wordgame(self, message, game):
        """Handle word game responses"""
        game_type = game['game_type']
        prompt = f"Continue the {game_type} game. Player said: '{message.content}'. Respond appropriately and keep the game going."
        
        response = await self.get_ai_response(prompt)
        
        await message.reply(response)

    async def _handle_mystery(self, message, game):
        """Handle mystery game responses"""
        prompt = f"Player wants to investigate: '{message.content}'. Provide clues or results of their investigation. Keep the mystery engaging."
        
        response = await self.get_ai_response(prompt)
        
        embed = discord.Embed(
            title="🔍 Investigation Results",
            description=response,
            color=0x8e44ad
        )
        await message.reply(embed=embed)

class RiddleView(discord.ui.View):
    def __init__(self, answer):
        super().__init__(timeout=300)
        self.answer = answer

    @discord.ui.button(label="Show Answer", style=discord.ButtonStyle.secondary, emoji="💡")
    async def show_answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💡 Answer",
            description=self.answer,
            color=0x2ecc71
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TriviaView(discord.ui.View):
    def __init__(self, correct_answer, explanation):
        super().__init__(timeout=300)
        self.correct_answer = correct_answer
        self.explanation = explanation

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def answer_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "A")

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def answer_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "B")

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def answer_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "C")

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def answer_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._check_answer(interaction, "D")

    async def _check_answer(self, interaction, choice):
        if choice == self.correct_answer:
            embed = discord.Embed(
                title="✅ Correct!",
                description=f"Well done! The answer was {choice}.\n\n{self.explanation}",
                color=0x2ecc71
            )
        else:
            embed = discord.Embed(
                title="❌ Incorrect",
                description=f"Sorry! The correct answer was {self.correct_answer}.\n\n{self.explanation}",
                color=0xe74c3c
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AIGames(bot))