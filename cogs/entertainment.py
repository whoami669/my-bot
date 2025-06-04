import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import aiohttp
import json

class Entertainment(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because of all of its problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
            "Why did the coffee file a police report? It got mugged!",
            "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!"
        ]
        
        joke = random.choice(jokes)
        embed = discord.Embed(
            title="😄 Random Joke",
            description=joke,
            color=discord.Color.yellow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fact", description="Get a random fun fact")
    async def fact(self, interaction: discord.Interaction):
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old!",
            "A group of flamingos is called a 'flamboyance'.",
            "Octopuses have three hearts and blue blood.",
            "Bananas are berries, but strawberries aren't.",
            "A single cloud can weigh more than a million pounds.",
            "There are more possible games of chess than atoms in the observable universe.",
            "Wombat poop is cube-shaped.",
            "The human brain uses about 20% of the body's total energy.",
            "A day on Venus is longer than its year.",
            "Sharks have been around longer than trees."
        ]
        
        fact = random.choice(facts)
        embed = discord.Embed(
            title="🧠 Fun Fact",
            description=fact,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quote", description="Get an inspirational quote")
    async def quote(self, interaction: discord.Interaction):
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
            ("Life is what happens to you while you're busy making other plans.", "John Lennon"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("It is during our darkest moments that we must focus to see the light.", "Aristotle"),
            ("The only impossible journey is the one you never begin.", "Tony Robbins"),
            ("Success is not final, failure is not fatal: it is the courage to continue that counts.", "Winston Churchill"),
            ("The way to get started is to quit talking and begin doing.", "Walt Disney"),
            ("Don't let yesterday take up too much of today.", "Will Rogers"),
            ("You learn more from failure than from success.", "Unknown")
        ]
        
        quote, author = random.choice(quotes)
        embed = discord.Embed(
            title="💭 Inspirational Quote",
            description=f'"{quote}"',
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"— {author}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="riddle", description="Get a riddle to solve")
    async def riddle(self, interaction: discord.Interaction):
        riddles = [
            ("I'm tall when I'm young, and short when I'm old. What am I?", "A candle"),
            ("What has keys but no locks, space but no room, and you can enter but not go inside?", "A keyboard"),
            ("What comes once in a minute, twice in a moment, but never in a thousand years?", "The letter M"),
            ("What has hands but cannot clap?", "A clock"),
            ("What gets wet while drying?", "A towel"),
            ("What can travel around the world while staying in a corner?", "A stamp"),
            ("What has a head and a tail but no body?", "A coin"),
            ("What goes up but never comes down?", "Your age"),
            ("What is so fragile that saying its name breaks it?", "Silence"),
            ("What can you break, even if you never pick it up or touch it?", "A promise")
        ]
        
        riddle, answer = random.choice(riddles)
        embed = discord.Embed(
            title="🧩 Riddle",
            description=riddle,
            color=discord.Color.orange()
        )
        embed.set_footer(text="Think you know the answer? React with 💡 to see it!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("💡")
        
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) == "💡" and reaction.message.id == message.id
        
        try:
            await self.bot.wait_for('reaction_add', check=check, timeout=30)
            answer_embed = discord.Embed(
                title="💡 Answer",
                description=answer,
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=answer_embed)
        except asyncio.TimeoutError:
            pass

    @app_commands.command(name="trivia", description="Answer a trivia question")
    async def trivia(self, interaction: discord.Interaction):
        questions = [
            ("What is the capital of France?", ["Paris", "London", "Berlin", "Madrid"], 0),
            ("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Saturn"], 1),
            ("What is the largest mammal in the world?", ["Elephant", "Blue Whale", "Giraffe", "Hippo"], 1),
            ("Who painted the Mona Lisa?", ["Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo"], 2),
            ("What is the chemical symbol for gold?", ["Go", "Gd", "Au", "Ag"], 2),
            ("Which is the smallest country in the world?", ["Monaco", "Vatican City", "San Marino", "Malta"], 1),
            ("What year did World War II end?", ["1944", "1945", "1946", "1947"], 1),
            ("What is the hardest natural substance on Earth?", ["Gold", "Iron", "Diamond", "Platinum"], 2),
            ("Which ocean is the largest?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3),
            ("What is the fastest land animal?", ["Lion", "Cheetah", "Leopard", "Tiger"], 1)
        ]
        
        question, options, correct = random.choice(questions)
        
        embed = discord.Embed(
            title="🧠 Trivia Question",
            description=question,
            color=discord.Color.blue()
        )
        
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        option_text = ""
        for i, option in enumerate(options):
            option_text += f"{reactions[i]} {option}\n"
        
        embed.add_field(name="Options", value=option_text, inline=False)
        embed.set_footer(text="You have 15 seconds to answer!")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        for i in range(len(options)):
            await message.add_reaction(reactions[i])
        
        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in reactions[:len(options)] and reaction.message.id == message.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=15)
            user_answer = reactions.index(str(reaction.emoji))
            
            if user_answer == correct:
                result_embed = discord.Embed(
                    title="✅ Correct!",
                    description=f"Great job! The answer is **{options[correct]}**",
                    color=discord.Color.green()
                )
            else:
                result_embed = discord.Embed(
                    title="❌ Incorrect",
                    description=f"The correct answer is **{options[correct]}**",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=result_embed)
            
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⏰ Time's Up!",
                description=f"The correct answer was **{options[correct]}**",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=timeout_embed)

    @app_commands.command(name="meme", description="Get a random meme (requires internet)")
    async def meme(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://meme-api.com/gimme') as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        embed = discord.Embed(
                            title=data['title'],
                            color=discord.Color.random()
                        )
                        embed.set_image(url=data['url'])
                        embed.set_footer(text=f"👍 {data['ups']} | r/{data['subreddit']}")
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("Sorry, couldn't fetch a meme right now!")
        except Exception:
            # Fallback to local meme text
            meme_texts = [
                "When you try to be productive but Discord exists",
                "Me: I'll just check Discord for 5 minutes\n*3 hours later*",
                "Discord servers at 3 AM: *becomes the most active*",
                "When someone @everyone's for something unimportant",
                "Trying to explain Discord to your parents"
            ]
            
            meme = random.choice(meme_texts)
            embed = discord.Embed(
                title="😂 Meme",
                description=meme,
                color=discord.Color.random()
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="roast", description="Get a playful roast")
    @app_commands.describe(user="User to roast (optional)")
    async def roast(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        roasts = [
            f"{target.mention}, you're like a software update. Whenever I see you, I think 'not now'.",
            f"{target.mention}, I'd explain it to you, but I don't have any crayons with me.",
            f"{target.mention}, you're not stupid; you just have bad luck thinking.",
            f"{target.mention}, if you were any more inbred, you'd be a sandwich.",
            f"{target.mention}, I'm jealous of people who don't know you.",
            f"{target.mention}, you're proof that evolution can go in reverse.",
            f"{target.mention}, I'd agree with you, but then we'd both be wrong.",
            f"{target.mention}, you're like the first slice of bread - everyone touches you, but nobody wants you.",
            f"{target.mention}, if ignorance is bliss, you must be the happiest person alive.",
            f"{target.mention}, you're not the dumbest person in the world, but you better hope they don't die."
        ]
        
        roast = random.choice(roasts)
        embed = discord.Embed(
            title="🔥 Roast",
            description=roast,
            color=discord.Color.red()
        )
        embed.set_footer(text="Just kidding! 😄")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="compliment", description="Give someone a nice compliment")
    @app_commands.describe(user="User to compliment (optional)")
    async def compliment(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        
        compliments = [
            f"{target.mention}, you're more fun than bubble wrap!",
            f"{target.mention}, you're like sunshine on a rainy day.",
            f"{target.mention}, you're someone's reason to smile today.",
            f"{target.mention}, you're proof that awesome people exist.",
            f"{target.mention}, you make everyone around you happier.",
            f"{target.mention}, you're incredibly thoughtful.",
            f"{target.mention}, you have great taste in Discord servers!",
            f"{target.mention}, you're more helpful than you realize.",
            f"{target.mention}, you're a true friend.",
            f"{target.mention}, you light up every room you enter!"
        ]
        
        compliment = random.choice(compliments)
        embed = discord.Embed(
            title="💝 Compliment",
            description=compliment,
            color=discord.Color.pink()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Entertainment(bot))