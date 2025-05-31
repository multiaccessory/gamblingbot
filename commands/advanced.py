"""
Advanced Discord Bot Commands
Contains advanced slash commands with subcommands, choices, and autocomplete functionality.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
import random
import json
import os

class AdvancedCommands(commands.Cog):
    """Advanced command cog with subcommands, choices, and autocomplete."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_profiles = {}  # Simple in-memory storage for demo
        
    # Command with choices
    @app_commands.command(name="roll", description="Roll dice with various options")
    @app_commands.describe(
        dice_type="Type of dice to roll",
        count="Number of dice to roll (1-10)"
    )
    @app_commands.choices(dice_type=[
        app_commands.Choice(name="4-sided (d4)", value="4"),
        app_commands.Choice(name="6-sided (d6)", value="6"),
        app_commands.Choice(name="8-sided (d8)", value="8"),
        app_commands.Choice(name="10-sided (d10)", value="10"),
        app_commands.Choice(name="12-sided (d12)", value="12"),
        app_commands.Choice(name="20-sided (d20)", value="20"),
        app_commands.Choice(name="100-sided (d100)", value="100")
    ])
    async def roll_dice(self, interaction: discord.Interaction, dice_type: str, count: int = 1):
        """Roll dice with specified type and count."""
        if count < 1 or count > 10:
            await interaction.response.send_message("Count must be between 1 and 10!", ephemeral=True)
            return
            
        sides = int(dice_type)
        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        
        embed = discord.Embed(
            title="🎲 Dice Roll Results",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name=f"{count}d{sides}",
            value=f"Results: {', '.join(map(str, results))}\nTotal: **{total}**",
            inline=False
        )
        
        if count > 1:
            embed.add_field(name="Average", value=f"{total/count:.1f}", inline=True)
            embed.add_field(name="Highest", value=str(max(results)), inline=True)
            embed.add_field(name="Lowest", value=str(min(results)), inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Command group with subcommands - renamed to avoid conflict
    settings_group = app_commands.Group(name="settings", description="Manage user settings")
    
    @settings_group.command(name="set", description="Set your profile information")
    @app_commands.describe(
        field="Profile field to set",
        value="Value to set for the field"
    )
    @app_commands.choices(field=[
        app_commands.Choice(name="Bio", value="bio"),
        app_commands.Choice(name="Favorite Game", value="game"),
        app_commands.Choice(name="Location", value="location"),
        app_commands.Choice(name="Hobby", value="hobby")
    ])
    async def settings_set(self, interaction: discord.Interaction, field: str, value: str):
        """Set a profile field."""
        user_id = str(interaction.user.id)
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
            
        self.user_profiles[user_id][field] = value
        
        embed = discord.Embed(
            title="✅ Setting Updated",
            description=f"Your {field} has been set to: **{value}**",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @settings_group.command(name="view", description="View profile information")
    @app_commands.describe(user="User whose profile to view (optional)")
    async def settings_view(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View a user's profile."""
        target_user = user or interaction.user
        user_id = str(target_user.id)
        
        if user_id not in self.user_profiles or not self.user_profiles[user_id]:
            embed = discord.Embed(
                title="📝 Profile",
                description=f"{target_user.display_name} hasn't set up their profile yet.",
                color=discord.Color.blue()
            )
        else:
            profile = self.user_profiles[user_id]
            embed = discord.Embed(
                title=f"📝 {target_user.display_name}'s Profile",
                color=discord.Color.blue()
            )
            
            for field, value in profile.items():
                embed.add_field(name=field.title(), value=value, inline=True)
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    
    @settings_group.command(name="clear", description="Clear your profile information")
    async def settings_clear(self, interaction: discord.Interaction):
        """Clear user's profile."""
        user_id = str(interaction.user.id)
        
        if user_id in self.user_profiles:
            del self.user_profiles[user_id]
        
        embed = discord.Embed(
            title="🗑️ Profile Cleared",
            description="Your profile has been cleared.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Command with autocomplete
    @app_commands.command(name="color", description="Get information about a color")
    @app_commands.describe(color_name="Name of the color")
    async def color_info(self, interaction: discord.Interaction, color_name: str):
        """Get information about a color."""
        colors = {
            "red": {"hex": "#FF0000", "rgb": "(255, 0, 0)", "description": "The color of passion and energy"},
            "blue": {"hex": "#0000FF", "rgb": "(0, 0, 255)", "description": "The color of calm and trust"},
            "green": {"hex": "#00FF00", "rgb": "(0, 255, 0)", "description": "The color of nature and growth"},
            "yellow": {"hex": "#FFFF00", "rgb": "(255, 255, 0)", "description": "The color of happiness and creativity"},
            "purple": {"hex": "#800080", "rgb": "(128, 0, 128)", "description": "The color of mystery and royalty"},
            "orange": {"hex": "#FFA500", "rgb": "(255, 165, 0)", "description": "The color of enthusiasm and warmth"},
            "pink": {"hex": "#FFC0CB", "rgb": "(255, 192, 203)", "description": "The color of love and compassion"},
            "black": {"hex": "#000000", "rgb": "(0, 0, 0)", "description": "The color of elegance and power"},
            "white": {"hex": "#FFFFFF", "rgb": "(255, 255, 255)", "description": "The color of purity and simplicity"},
            "gray": {"hex": "#808080", "rgb": "(128, 128, 128)", "description": "The color of balance and neutrality"}
        }
        
        color_name = color_name.lower()
        
        if color_name not in colors:
            embed = discord.Embed(
                title="❌ Color Not Found",
                description=f"Sorry, I don't have information about the color '{color_name}'.",
                color=discord.Color.red()
            )
            
            # Suggest similar colors
            suggestions = [name for name in colors.keys() if color_name in name or name in color_name]
            if suggestions:
                embed.add_field(
                    name="Did you mean?",
                    value=", ".join(suggestions[:3]),
                    inline=False
                )
        else:
            color_info = colors[color_name]
            
            # Convert hex to int for embed color
            hex_value = color_info["hex"].lstrip('#')
            color_int = int(hex_value, 16) if hex_value != "000000" else 0x36393F  # Discord doesn't show pure black
            
            embed = discord.Embed(
                title=f"🎨 {color_name.title()}",
                description=color_info["description"],
                color=color_int
            )
            
            embed.add_field(name="Hex Code", value=color_info["hex"], inline=True)
            embed.add_field(name="RGB", value=color_info["rgb"], inline=True)
            embed.add_field(name="Color", value="█████", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @color_info.autocomplete('color_name')
    async def color_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete for color names."""
        colors = ["red", "blue", "green", "yellow", "purple", "orange", "pink", "black", "white", "gray"]
        
        # Filter colors based on current input
        matching_colors = [color for color in colors if current.lower() in color.lower()]
        
        # Return as choices (max 25)
        return [
            app_commands.Choice(name=color.title(), value=color)
            for color in matching_colors[:25]
        ]

    # Advanced command with multiple subcommands and choices
    moderation_group = app_commands.Group(name="mod", description="Moderation commands")
    
    @moderation_group.command(name="timeout", description="Timeout a user")
    @app_commands.describe(
        user="User to timeout",
        duration="Duration of timeout",
        reason="Reason for timeout"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="1 minute", value="60"),
        app_commands.Choice(name="5 minutes", value="300"),
        app_commands.Choice(name="10 minutes", value="600"),
        app_commands.Choice(name="30 minutes", value="1800"),
        app_commands.Choice(name="1 hour", value="3600"),
        app_commands.Choice(name="6 hours", value="21600"),
        app_commands.Choice(name="12 hours", value="43200"),
        app_commands.Choice(name="1 day", value="86400")
    ])
    async def mod_timeout(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str = "No reason provided"):
        """Timeout a user (demonstration only - doesn't actually timeout)."""
        # Check permissions (only works in servers)
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to timeout members.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Convert duration to readable format
        duration_seconds = int(duration)
        if duration_seconds < 60:
            duration_text = f"{duration_seconds} seconds"
        elif duration_seconds < 3600:
            duration_text = f"{duration_seconds // 60} minutes"
        elif duration_seconds < 86400:
            duration_text = f"{duration_seconds // 3600} hours"
        else:
            duration_text = f"{duration_seconds // 86400} days"
        
        embed = discord.Embed(
            title="⏰ User Timeout (Demo)",
            description=f"Would timeout {user.mention} for {duration_text}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text="This is a demonstration - no actual timeout was applied")
        
        await interaction.response.send_message(embed=embed)
    
    @moderation_group.command(name="warn", description="Warn a user")
    @app_commands.describe(
        user="User to warn",
        severity="Warning severity",
        reason="Reason for warning"
    )
    @app_commands.choices(severity=[
        app_commands.Choice(name="Low - Minor infraction", value="low"),
        app_commands.Choice(name="Medium - Moderate infraction", value="medium"),
        app_commands.Choice(name="High - Serious infraction", value="high"),
        app_commands.Choice(name="Critical - Severe infraction", value="critical")
    ])
    async def mod_warn(self, interaction: discord.Interaction, user: discord.Member, severity: str, reason: str):
        """Warn a user (demonstration only)."""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.moderate_members:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to warn members.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        severity_colors = {
            "low": discord.Color.green(),
            "medium": discord.Color.yellow(),
            "high": discord.Color.orange(),
            "critical": discord.Color.red()
        }
        
        severity_emojis = {
            "low": "⚠️",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🔴"
        }
        
        embed = discord.Embed(
            title=f"{severity_emojis[severity]} User Warning (Demo)",
            description=f"Warning issued to {user.mention}",
            color=severity_colors[severity]
        )
        embed.add_field(name="Severity", value=severity.title(), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text="This is a demonstration - no actual warning was recorded")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(AdvancedCommands(bot))