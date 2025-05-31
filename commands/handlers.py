"""
Enhanced Error Handlers and Event Listeners
Contains comprehensive error handling and event management for the Discord bot.
"""

import discord
from discord.ext import commands
import traceback
import logging
import asyncio
import random
from datetime import datetime

class EnhancedHandlers(commands.Cog):
    """Enhanced error handling and event listeners."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Enhanced on_ready event with detailed logging."""
        self.logger.info(f"Bot is ready! Logged in as {self.bot.user}")
        
        # Set enhanced bot presence
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name=f"🎰 Gambling | /help | Serving {len(self.bot.guilds)} servers"
        )
        await self.bot.change_presence(activity=activity, status=discord.Status.online)
        
        # Log detailed bot information
        total_members = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
        self.logger.info(f"Bot statistics: {len(self.bot.guilds)} guilds, {total_members} total members")
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎰 GAMBLING BOT READY 🎰                  ║
╠══════════════════════════════════════════════════════════════╣
║  Bot: {self.bot.user.name:<48} ║
║  ID: {self.bot.user.id:<49} ║
║  Guilds: {len(self.bot.guilds):<46} ║
║  Members: {total_members:<45} ║
║  Commands: {len([cmd for cmd in self.bot.tree.walk_commands()]):<44} ║
╚══════════════════════════════════════════════════════════════╝
        """)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Handle bot joining a new guild."""
        self.logger.info(f"Joined guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
        
        # Update bot presence
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name=f"🎰 Gambling | /help | Serving {len(self.bot.guilds)} servers"
        )
        await self.bot.change_presence(activity=activity)
        
        # Try to send a welcome message to the system channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🎰 Thanks for adding me!",
                description="Welcome to the ultimate Discord gambling experience!",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="🚀 Get Started",
                value="Use `/help` to see all available commands\nStart with `/daily` to get your first cash reward!",
                inline=False
            )
            embed.add_field(
                name="🎮 Available Games",
                value="Slots, Blackjack, Roulette, Coinflip, Dice, Racing and more!",
                inline=False
            )
            embed.add_field(
                name="💡 Pro Tips",
                value="• Use `/profile` to track your progress\n• Check `/leaderboard` to compete with others\n• Both slash commands (/) and prefix commands work!",
                inline=False
            )
            
            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Handle bot leaving a guild."""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update bot presence
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name=f"🎰 Gambling | /help | Serving {len(self.bot.guilds)} servers"
        )
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Enhanced error handling for traditional prefix commands."""
        # Ignore if command has local error handler
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Ignore if cog has error handler and it was handled
        if ctx.cog and ctx.cog.has_error_handler():
            return
        
        # Handle specific error types
        if isinstance(error, commands.CommandNotFound):
            # Suggest using help command
            embed = discord.Embed(
                title="❓ Command Not Found",
                description=f"Command `{ctx.invoked_with}` not found. Use `{ctx.prefix}help` to see available commands.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param.name}`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}{ctx.command.name} {ctx.command.signature}`",
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description="One or more arguments are invalid.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage",
                value=f"`{ctx.prefix}{ctx.command.name} {ctx.command.signature}`",
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.CommandOnCooldown):
            # Format cooldown time nicely
            remaining = int(error.retry_after)
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_format = []
            if hours > 0:
                time_format.append(f"{hours}h")
            if minutes > 0:
                time_format.append(f"{minutes}m")
            if seconds > 0:
                time_format.append(f"{seconds}s")
            
            time_str = " ".join(time_format) if time_format else "a few seconds"
            
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {time_str}.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join([f"`{perm}`" for perm in error.missing_permissions]),
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="🤖 Bot Missing Permissions",
                description="I don't have the necessary permissions to execute this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join([f"`{perm}`" for perm in error.missing_permissions]),
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="🏠 Server Only Command",
                description="This command can only be used in a server, not in DMs.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.DisabledCommand):
            embed = discord.Embed(
                title="🚫 Command Disabled",
                description="This command is currently disabled.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            
        else:
            # Log unexpected errors
            self.logger.error(f"Unexpected error in command {ctx.command}: {error}")
            self.logger.error(traceback.format_exc())
            
            embed = discord.Embed(
                title="💥 Unexpected Error",
                description="An unexpected error occurred. The issue has been logged.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Enhanced error handling for slash commands."""
        self.logger.error(f"Slash command error in {interaction.command}: {error}")
        
        # Create appropriate error message
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            remaining = int(error.retry_after)
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_format = []
            if hours > 0:
                time_format.append(f"{hours}h")
            if minutes > 0:
                time_format.append(f"{minutes}m")
            if seconds > 0:
                time_format.append(f"{seconds}s")
            
            time_str = " ".join(time_format) if time_format else "a few seconds"
            
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"This command is on cooldown. Try again in {time_str}.",
                color=discord.Color.orange()
            )
            
        elif isinstance(error, discord.app_commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed = discord.Embed(
                title="🤖 Bot Missing Permissions",
                description="I don't have the necessary permissions to execute this command.",
                color=discord.Color.red()
            )
            
        else:
            embed = discord.Embed(
                title="💥 Command Error",
                description="An error occurred while processing your command.",
                color=discord.Color.red()
            )
            
            # Log the full error for debugging
            self.logger.error(traceback.format_exc())
        
        # Respond appropriately based on interaction state
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Enhanced message handling with smart suggestions."""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Don't interfere with commands
        if message.content.startswith(('/', '!', '$', '?', '.')):
            return
        
        # Smart gambling suggestions for certain keywords
        gambling_keywords = ['gamble', 'bet', 'casino', 'slots', 'blackjack', 'money', 'cash']
        content_lower = message.content.lower()
        
        if any(keyword in content_lower for keyword in gambling_keywords):
            # Small chance to suggest gambling commands
            if len(content_lower) > 10 and 'how' in content_lower and random.choice([True, False, False, False]):  # 25% chance
                embed = discord.Embed(
                    title="🎰 Looking to gamble?",
                    description="Try our gambling commands!",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="Quick Start",
                    value="`/daily` - Get free money\n`/slots` - Try the slot machine\n`/help` - See all commands",
                    inline=False
                )
                
                try:
                    await message.channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.command(name='status', hidden=True)
    @commands.is_owner()
    async def status_command(self, ctx):
        """Show detailed bot status (owner only)."""
        embed = discord.Embed(
            title="🤖 Bot Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Bot info
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Latency", value=f"{self.bot.latency*1000:.2f}ms", inline=True)
        
        # Server info
        total_members = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Commands", value=len([cmd for cmd in self.bot.tree.walk_commands()]), inline=True)
        
        # System info
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        embed.add_field(name="Memory Usage", value=f"{memory_usage:.1f} MB", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Uptime", value=str(datetime.utcnow() - self.bot.start_time).split('.')[0], inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(EnhancedHandlers(bot))