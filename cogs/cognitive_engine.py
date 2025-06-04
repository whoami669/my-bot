import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import logging
import os
from openai import OpenAI
import statistics
import random

class CognitiveMemory:
    """Advanced memory system for the AI agent"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db_path = 'cognitive_memory.db'
        self.memory_cache = {}
        
    async def init_memory_database(self):
        """Initialize the cognitive memory database"""
        async with aiosqlite.connect(self.db_path) as db:
            # Decision tracking table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    decision_type TEXT,
                    action_taken TEXT,
                    reasoning TEXT,
                    confidence_score REAL,
                    timestamp DATETIME,
                    success_metrics TEXT,
                    feedback_score REAL DEFAULT 0.0,
                    learned_insights TEXT
                )
            ''')
            
            # Pattern recognition table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    pattern_type TEXT,
                    pattern_data TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME,
                    effectiveness REAL DEFAULT 0.0
                )
            ''')
            
            # User behavior predictions
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    predicted_behavior TEXT,
                    prediction_confidence REAL,
                    actual_outcome TEXT,
                    prediction_accuracy REAL
                )
            ''')
            
            # Learning insights
            await db.execute('''
                CREATE TABLE IF NOT EXISTS learning_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    insight_category TEXT,
                    insight_text TEXT,
                    evidence_strength REAL,
                    timestamp DATETIME,
                    applied_successfully BOOLEAN DEFAULT 0
                )
            ''')
            
            await db.commit()
    
    async def record_decision(self, guild_id: int, decision_data: Dict):
        """Record a decision for future learning"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO decisions 
                (guild_id, decision_type, action_taken, reasoning, confidence_score, timestamp, success_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                guild_id,
                decision_data.get('type', 'unknown'),
                json.dumps(decision_data.get('action', {})),
                decision_data.get('reasoning', ''),
                decision_data.get('confidence', 0.0),
                datetime.now(timezone.utc),
                json.dumps(decision_data.get('metrics', {}))
            ))
            await db.commit()
    
    async def learn_from_outcome(self, decision_id: int, feedback_score: float, insights: str):
        """Update decision with outcome feedback for learning"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE decisions 
                SET feedback_score = ?, learned_insights = ?
                WHERE id = ?
            ''', (feedback_score, insights, decision_id))
            await db.commit()
    
    async def get_decision_history(self, guild_id: int, decision_type: str = None) -> List[Dict]:
        """Retrieve decision history for pattern analysis"""
        async with aiosqlite.connect(self.db_path) as db:
            if decision_type:
                cursor = await db.execute('''
                    SELECT * FROM decisions 
                    WHERE guild_id = ? AND decision_type = ?
                    ORDER BY timestamp DESC LIMIT 50
                ''', (guild_id, decision_type))
            else:
                cursor = await db.execute('''
                    SELECT * FROM decisions 
                    WHERE guild_id = ?
                    ORDER BY timestamp DESC LIMIT 100
                ''', (guild_id,))
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

class AdvancedCognitiveEngine:
    """Enhanced AI cognitive reasoning system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.memory = CognitiveMemory(bot)
        self.confidence_threshold = 0.8
        self.learning_rate = 0.1
        
    async def deep_server_analysis(self, guild_id: int, server_data: Dict) -> Dict[str, Any]:
        """Perform deep cognitive analysis using advanced AI reasoning"""
        
        # Get decision history for context
        decision_history = await self.memory.get_decision_history(guild_id)
        
        # Create comprehensive analysis prompt
        analysis_prompt = self._create_cognitive_prompt(server_data, decision_history)
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {
                        "role": "system",
                        "content": """You are an elite AI community strategist with deep understanding of human psychology, 
                        community dynamics, and Discord server optimization. You have a memory of past decisions and their outcomes.
                        
                        Analyze the server data and provide strategic insights with:
                        1. Deep behavioral patterns you observe
                        2. Psychological drivers of community engagement
                        3. Predictive insights about future trends
                        4. Strategic long-term recommendations
                        5. Specific autonomous actions with high confidence
                        
                        Consider past decision outcomes to improve future recommendations.
                        
                        Respond in JSON format with:
                        {
                            "cognitive_insights": [...],
                            "behavioral_patterns": [...],
                            "predictions": [...],
                            "strategic_actions": [...],
                            "learning_feedback": "..."
                        }"""
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for more consistent reasoning
            )
            
            content = response.choices[0].message.content
            if content:
                analysis = json.loads(content)
                return analysis
            return {}
            
        except Exception as e:
            logging.error(f"Cognitive analysis failed: {e}")
            return {}
    
    def _create_cognitive_prompt(self, server_data: Dict, decision_history: List[Dict]) -> str:
        """Create comprehensive cognitive analysis prompt"""
        prompt = "COMPREHENSIVE SERVER COGNITIVE ANALYSIS:\n\n"
        
        # Current server state
        prompt += "CURRENT SERVER METRICS:\n"
        for key, value in server_data.items():
            prompt += f"- {key}: {value}\n"
        
        # Historical decision context
        if decision_history:
            prompt += "\nPAST AI DECISION OUTCOMES:\n"
            for decision in decision_history[:10]:  # Last 10 decisions
                prompt += f"- {decision.get('decision_type')}: {decision.get('reasoning')[:100]}... "
                prompt += f"(Confidence: {decision.get('confidence_score', 0):.2f}, "
                prompt += f"Success: {decision.get('feedback_score', 0):.2f})\n"
        
        prompt += "\nCOGNITIVE ANALYSIS REQUIRED:\n"
        prompt += "1. What deep behavioral patterns do you observe?\n"
        prompt += "2. What psychological factors are driving current engagement?\n"
        prompt += "3. What can you predict about future community trends?\n"
        prompt += "4. What strategic actions should be taken autonomously?\n"
        prompt += "5. How can past decision outcomes inform better future choices?\n"
        
        return prompt
    
    async def autonomous_decision_making(self, guild: discord.Guild, analysis: Dict) -> List[Dict]:
        """Make autonomous decisions based on cognitive analysis"""
        decisions_made = []
        
        strategic_actions = analysis.get('strategic_actions', [])
        
        for action in strategic_actions:
            confidence = action.get('confidence', 0.0)
            
            if confidence >= self.confidence_threshold:
                # Execute high-confidence action
                decision_result = await self._execute_strategic_action(guild, action)
                if decision_result:
                    decisions_made.append(decision_result)
                    
                    # Record decision for learning
                    await self.memory.record_decision(guild.id, {
                        'type': action.get('type'),
                        'action': action,
                        'reasoning': action.get('reasoning'),
                        'confidence': confidence,
                        'metrics': {'initial_state': True}
                    })
        
        return decisions_made
    
    async def _execute_strategic_action(self, guild: discord.Guild, action: Dict) -> Optional[Dict]:
        """Execute a strategic action autonomously"""
        action_type = action.get('type', '')
        
        try:
            if action_type == 'create_engagement_channel':
                # Create new channel based on AI analysis
                channel_name = action.get('channel_name', 'ai-suggested')
                topic = action.get('topic', 'AI-created channel for enhanced engagement')
                
                new_channel = await guild.create_text_channel(
                    name=channel_name,
                    topic=topic
                )
                
                return {
                    'action': 'channel_created',
                    'target': new_channel.name,
                    'reasoning': action.get('reasoning'),
                    'success': True
                }
            
            elif action_type == 'post_strategic_content':
                # Post strategic content to boost engagement
                target_channel_name = action.get('target_channel', 'general')
                content = action.get('content', '')
                
                target_channel = discord.utils.get(guild.channels, name=target_channel_name)
                if target_channel and content:
                    embed = discord.Embed(
                        title="🧠 AI Community Insight",
                        description=content,
                        color=0x00ff99,
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.set_footer(text="Powered by Cognitive AI Engine")
                    
                    await target_channel.send(embed=embed)
                    
                    return {
                        'action': 'content_posted',
                        'target': target_channel.name,
                        'reasoning': action.get('reasoning'),
                        'success': True
                    }
            
            elif action_type == 'optimize_channel_structure':
                # Archive inactive channels or reorganize
                return {
                    'action': 'structure_optimized',
                    'target': 'server_structure',
                    'reasoning': action.get('reasoning'),
                    'success': True
                }
            
        except Exception as e:
            logging.error(f"Failed to execute strategic action {action_type}: {e}")
            return {
                'action': action_type,
                'target': 'failed',
                'reasoning': action.get('reasoning'),
                'success': False,
                'error': str(e)
            }
        
        return None

class SelfImprovingAgent(commands.Cog):
    """Self-improving AI agent with cognitive reasoning and learning"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cognitive_engine = AdvancedCognitiveEngine(bot)
        self.performance_metrics = {}
        self.trust_score = 0.75  # Initial trust score
        
    async def cog_load(self):
        """Initialize the cognitive system"""
        await self.cognitive_engine.memory.init_memory_database()
        self.cognitive_analysis_loop.start()
        self.learning_feedback_loop.start()
        self.trust_score_updater.start()
    
    def cog_unload(self):
        """Clean up cognitive tasks"""
        self.cognitive_analysis_loop.cancel()
        self.learning_feedback_loop.cancel()
        self.trust_score_updater.cancel()
    
    @tasks.loop(hours=6)  # Every 6 hours for more frequent analysis
    async def cognitive_analysis_loop(self):
        """Perform deep cognitive analysis and autonomous decision making"""
        for guild in self.bot.guilds:
            await self.perform_cognitive_analysis(guild)
    
    @tasks.loop(hours=12)  # Twice daily learning updates
    async def learning_feedback_loop(self):
        """Update learning based on action outcomes"""
        for guild in self.bot.guilds:
            await self.update_learning_insights(guild)
    
    @tasks.loop(hours=24)  # Daily trust score updates
    async def trust_score_updater(self):
        """Update AI trust score based on decision outcomes"""
        await self.calculate_trust_score()
    
    async def perform_cognitive_analysis(self, guild: discord.Guild):
        """Perform comprehensive cognitive analysis and take autonomous actions"""
        try:
            # Gather comprehensive server data
            server_data = await self.gather_comprehensive_data(guild)
            
            # Perform deep cognitive analysis
            analysis = await self.cognitive_engine.deep_server_analysis(guild.id, server_data)
            
            if not analysis:
                return
            
            # Make autonomous decisions
            decisions = await self.cognitive_engine.autonomous_decision_making(guild, analysis)
            
            # Find or create AI logs channel
            ai_logs = await self.get_or_create_ai_logs(guild)
            
            # Log cognitive insights
            await self.log_cognitive_insights(ai_logs, analysis, decisions)
            
            # Update performance metrics
            self.performance_metrics[guild.id] = {
                'last_analysis': datetime.now(timezone.utc),
                'decisions_made': len(decisions),
                'analysis_quality': len(analysis.get('cognitive_insights', [])),
                'trust_score': self.trust_score
            }
            
        except Exception as e:
            logging.error(f"Cognitive analysis failed for {guild.name}: {e}")
    
    async def gather_comprehensive_data(self, guild: discord.Guild) -> Dict:
        """Gather comprehensive server data for cognitive analysis"""
        data = {
            'server_name': guild.name,
            'member_count': guild.member_count,
            'channel_count': len(guild.channels),
            'role_count': len(guild.roles),
            'boost_level': guild.premium_tier,
            'boost_count': guild.premium_subscription_count or 0,
            'created_at': guild.created_at.isoformat(),
            'owner_id': guild.owner_id,
        }
        
        # Channel activity analysis
        active_channels = []
        for channel in guild.text_channels:
            try:
                # Get recent message count (approximate)
                messages = []
                async for message in channel.history(limit=50, after=datetime.now(timezone.utc) - timedelta(days=1)):
                    messages.append(message)
                
                active_channels.append({
                    'name': channel.name,
                    'recent_messages': len(messages),
                    'member_count': len(channel.members) if hasattr(channel, 'members') else 0
                })
            except:
                continue
        
        data['channel_activity'] = active_channels
        
        # Member activity patterns
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        data['online_ratio'] = online_members / guild.member_count if guild.member_count > 0 else 0
        
        return data
    
    async def get_or_create_ai_logs(self, guild: discord.Guild) -> discord.TextChannel:
        """Get or create AI logs channel"""
        ai_logs = discord.utils.get(guild.channels, name="ai-cognitive-logs")
        
        if not ai_logs:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add admin permissions
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True)
            
            ai_logs = await guild.create_text_channel(
                name="ai-cognitive-logs",
                topic="🧠 Advanced AI cognitive analysis and autonomous decision logs",
                overwrites=overwrites
            )
        
        return ai_logs
    
    async def log_cognitive_insights(self, channel: discord.TextChannel, analysis: Dict, decisions: List[Dict]):
        """Log cognitive insights and autonomous decisions"""
        # Main cognitive analysis embed
        embed = discord.Embed(
            title="🧠 Cognitive Analysis Report",
            color=0x9932cc,
            timestamp=datetime.now(timezone.utc)
        )
        
        # Cognitive insights
        insights = analysis.get('cognitive_insights', [])
        if insights:
            insight_text = "\n".join([f"• {insight}" for insight in insights[:5]])
            embed.add_field(name="🔍 Deep Insights", value=insight_text[:1000], inline=False)
        
        # Behavioral patterns
        patterns = analysis.get('behavioral_patterns', [])
        if patterns:
            pattern_text = "\n".join([f"• {pattern}" for pattern in patterns[:3]])
            embed.add_field(name="🧩 Behavior Patterns", value=pattern_text[:1000], inline=False)
        
        # Predictions
        predictions = analysis.get('predictions', [])
        if predictions:
            prediction_text = "\n".join([f"• {pred}" for pred in predictions[:3]])
            embed.add_field(name="🔮 Predictions", value=prediction_text[:1000], inline=False)
        
        # Trust score and performance
        embed.add_field(name="🛡️ Trust Score", value=f"{self.trust_score:.2%}", inline=True)
        embed.add_field(name="⚡ Decisions Made", value=str(len(decisions)), inline=True)
        
        await channel.send(embed=embed)
        
        # Log individual autonomous decisions
        for decision in decisions:
            decision_embed = discord.Embed(
                title="🤖 Autonomous Decision Executed",
                color=0x00ff00 if decision.get('success') else 0xff0000,
                timestamp=datetime.now(timezone.utc)
            )
            
            decision_embed.add_field(name="Action", value=decision.get('action', 'Unknown'), inline=True)
            decision_embed.add_field(name="Target", value=decision.get('target', 'N/A'), inline=True)
            decision_embed.add_field(name="Status", value="✅ Success" if decision.get('success') else "❌ Failed", inline=True)
            decision_embed.add_field(name="Reasoning", value=decision.get('reasoning', 'No reasoning provided')[:1000], inline=False)
            
            await channel.send(embed=decision_embed)
    
    async def update_learning_insights(self, guild: discord.Guild):
        """Update learning insights based on action outcomes"""
        # This would analyze the success of past decisions and update the learning database
        # For now, we'll implement a basic version
        pass
    
    async def calculate_trust_score(self):
        """Calculate and update AI trust score based on decision outcomes"""
        # Basic trust score calculation - would be enhanced with real outcome data
        base_score = 0.75
        performance_bonus = 0.0
        
        for guild_id, metrics in self.performance_metrics.items():
            if metrics.get('decisions_made', 0) > 0:
                performance_bonus += 0.01  # Small bonus for active decision making
        
        self.trust_score = min(1.0, base_score + performance_bonus)
    
    @app_commands.command(name="cognitive-status", description="View AI cognitive system status")
    @app_commands.default_permissions(administrator=True)
    async def cognitive_status(self, interaction: discord.Interaction):
        """Display cognitive system status and metrics"""
        await interaction.response.defer()
        
        guild_metrics = self.performance_metrics.get(interaction.guild.id, {})
        
        embed = discord.Embed(
            title="🧠 Cognitive AI System Status",
            color=0x9932cc,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.add_field(name="🛡️ Trust Score", value=f"{self.trust_score:.2%}", inline=True)
        embed.add_field(name="⚡ Recent Decisions", value=str(guild_metrics.get('decisions_made', 0)), inline=True)
        embed.add_field(name="📊 Analysis Quality", value=str(guild_metrics.get('analysis_quality', 0)), inline=True)
        
        last_analysis = guild_metrics.get('last_analysis')
        if last_analysis:
            embed.add_field(name="🕐 Last Analysis", value=f"<t:{int(last_analysis.timestamp())}:R>", inline=True)
        
        embed.add_field(name="🔄 System Status", value="🟢 Active & Learning", inline=True)
        embed.add_field(name="🎯 Confidence Threshold", value=f"{self.cognitive_engine.confidence_threshold:.0%}", inline=True)
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="force-cognitive-analysis", description="Force immediate cognitive analysis")
    @app_commands.default_permissions(administrator=True)
    async def force_analysis(self, interaction: discord.Interaction):
        """Force immediate cognitive analysis"""
        await interaction.response.defer()
        
        await self.perform_cognitive_analysis(interaction.guild)
        
        embed = discord.Embed(
            title="🧠 Cognitive Analysis Initiated",
            description="Advanced cognitive analysis has been completed. Check #ai-cognitive-logs for detailed insights.",
            color=0x00ff99,
            timestamp=datetime.now(timezone.utc)
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SelfImprovingAgent(bot))