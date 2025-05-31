"""
Discord Bot Main Class
Contains the main bot logic, event handlers, and command loading functionality.
"""

import logging
import discord
from discord.ext import commands
from datetime import datetime
import traceback

from config import BotConfig
from commands.basic import BasicCommands
from commands.advanced import AdvancedCommands
from commands.gambling import GamblingCommands
from commands.games import GamesCommands
from commands.leaderboard import LeaderboardCommands
from commands.visual_slots import VisualSlotsCommands
from commands.traditional import TraditionalCommands
from commands.handlers import EnhancedHandlers

class DiscordBot(commands.Bot):
    """Main Discord bot class with slash command support."""
    
    def __init__(self):
        """Initialize the Discord bot with proper intents and configuration."""
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        # Initialize the bot
        super().__init__(
            command_prefix=BotConfig.COMMAND_PREFIX,
            intents=intents,
            help_command=None,  # We'll create our own help command
            case_insensitive=True
        )
        
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.utcnow()
        
    async def setup_hook(self):
        """Setup hook called when the bot is starting up."""
        self.logger.info("Setting up bot...")
        
        # Add command cogs
        await self.add_cog(BasicCommands(self))
        await self.add_cog(AdvancedCommands(self))
        await self.add_cog(GamblingCommands(self))
        await self.add_cog(GamesCommands(self))
        await self.add_cog(LeaderboardCommands(self))
        await self.add_cog(VisualSlotsCommands(self))
        await self.add_cog(TraditionalCommands(self))
        await self.add_cog(EnhancedHandlers(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Event triggered when the bot is ready and connected."""
        if self.user:
            self.logger.info(f"Bot is ready! Logged in as {self.user.name} (ID: {self.user.id})")
        self.logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)
    
    async def on_guild_join(self, guild):
        """Event triggered when the bot joins a new guild."""
        self.logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_remove(self, guild):
        """Event triggered when the bot leaves a guild."""
        self.logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        
        # Update bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(self.guilds)} servers | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for traditional commands."""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        
        self.logger.error(f"Command error in {ctx.command}: {error}")
        
        # Send error message to user
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred while executing the command: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global error handler for slash commands."""
        self.logger.error(f"Slash command error: {error}")
        self.logger.error(traceback.format_exc())
        
        # Create error embed
        embed = discord.Embed(
            title="❌ Command Error",
            description="An error occurred while processing your command.",
            color=discord.Color.red()
        )
        
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            embed.description = f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            embed.description = "You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed.description = "I don't have the necessary permissions to execute this command."
        else:
            embed.description = f"An unexpected error occurred: {str(error)}"
        
        # Respond to the interaction
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")
    
    async def on_error(self, event, *args, **kwargs):
        """Global error handler for other events."""
        self.logger.error(f"Error in event {event}: {traceback.format_exc()}")
