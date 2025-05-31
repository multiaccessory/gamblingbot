"""
Leaderboard and Statistics Commands
Contains leaderboard functionality and player statistics tracking.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
import json
import os
from datetime import datetime

class LeaderboardCommands(commands.Cog):
    """Leaderboard and statistics command cog."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.load_user_data()
        
    def load_user_data(self):
        """Load user data from file if it exists."""
        try:
            if os.path.exists('user_data.json'):
                with open('user_data.json', 'r') as f:
                    self.user_data = json.load(f)
        except Exception:
            self.user_data = {}
    
    def save_user_data(self):
        """Save user data to file."""
        try:
            with open('user_data.json', 'w') as f:
                json.dump(self.user_data, f, indent=2)
        except Exception:
            pass
    
    def get_user_profile(self, user_id: str):
        """Get or create user profile."""
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'cash': 1000,
                'level': 0,
                'xp': 0,
                'wins': 0,
                'losses': 0,
                'total_bet': 0,
                'total_won': 0,
                'last_daily': None,
                'last_work': None,
                'achievements': {},
                'items': {},
                'boosts': {}
            }
        return self.user_data[user_id]

    # Leaderboard command group
    leaderboard_group = app_commands.Group(name="leaderboard", description="View leaderboards and rankings")
    
    @leaderboard_group.command(name="cash", description="View the richest players")
    @app_commands.describe(scope="Show server or global leaderboard")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Server Only", value="server"),
        app_commands.Choice(name="Global", value="global")
    ])
    async def leaderboard_cash(self, interaction: discord.Interaction, scope: str = "server"):
        """Show cash leaderboard."""
        self.load_user_data()
        
        # Get all users with their cash amounts
        user_cash = []
        for user_id, profile in self.user_data.items():
            try:
                user = self.bot.get_user(int(user_id))
                if user:
                    # If server scope, only include users from this server
                    if scope == "server" and interaction.guild:
                        member = interaction.guild.get_member(int(user_id))
                        if not member:
                            continue
                    
                    user_cash.append((user, profile['cash']))
            except (ValueError, KeyError):
                continue
        
        # Sort by cash (descending)
        user_cash.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 10
        top_users = user_cash[:10]
        
        if not top_users:
            embed = discord.Embed(
                title="💰 Cash Leaderboard",
                description="No players found with gambling data.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"💰 Cash Leaderboard ({'Server' if scope == 'server' else 'Global'})",
            color=discord.Color.gold()
        )
        
        description_lines = []
        for i, (user, cash) in enumerate(top_users):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            description_lines.append(f"{medal} **{user.display_name}** - ${cash:,}")
        
        embed.description = "\n".join(description_lines)
        
        # Add user's ranking if not in top 10
        user_rank = None
        for i, (user, cash) in enumerate(user_cash):
            if user.id == interaction.user.id:
                user_rank = i + 1
                break
        
        if user_rank and user_rank > 10:
            embed.add_field(
                name="Your Ranking",
                value=f"#{user_rank} - ${self.get_user_profile(str(interaction.user.id))['cash']:,}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @leaderboard_group.command(name="level", description="View highest level players")
    @app_commands.describe(scope="Show server or global leaderboard")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Server Only", value="server"),
        app_commands.Choice(name="Global", value="global")
    ])
    async def leaderboard_level(self, interaction: discord.Interaction, scope: str = "server"):
        """Show level leaderboard."""
        self.load_user_data()
        
        # Get all users with their levels
        user_levels = []
        for user_id, profile in self.user_data.items():
            try:
                user = self.bot.get_user(int(user_id))
                if user:
                    # If server scope, only include users from this server
                    if scope == "server" and interaction.guild:
                        member = interaction.guild.get_member(int(user_id))
                        if not member:
                            continue
                    
                    user_levels.append((user, profile['level'], profile['xp']))
            except (ValueError, KeyError):
                continue
        
        # Sort by level first, then XP (descending)
        user_levels.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Take top 10
        top_users = user_levels[:10]
        
        if not top_users:
            embed = discord.Embed(
                title="⭐ Level Leaderboard",
                description="No players found with gambling data.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⭐ Level Leaderboard ({'Server' if scope == 'server' else 'Global'})",
            color=discord.Color.purple()
        )
        
        description_lines = []
        for i, (user, level, xp) in enumerate(top_users):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            description_lines.append(f"{medal} **{user.display_name}** - Level {level} ({xp:,} XP)")
        
        embed.description = "\n".join(description_lines)
        
        # Add user's ranking if not in top 10
        user_rank = None
        for i, (user, level, xp) in enumerate(user_levels):
            if user.id == interaction.user.id:
                user_rank = i + 1
                break
        
        if user_rank and user_rank > 10:
            profile = self.get_user_profile(str(interaction.user.id))
            embed.add_field(
                name="Your Ranking",
                value=f"#{user_rank} - Level {profile['level']} ({profile['xp']:,} XP)",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @leaderboard_group.command(name="wins", description="View players with most wins")
    @app_commands.describe(scope="Show server or global leaderboard")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Server Only", value="server"),
        app_commands.Choice(name="Global", value="global")
    ])
    async def leaderboard_wins(self, interaction: discord.Interaction, scope: str = "server"):
        """Show wins leaderboard."""
        self.load_user_data()
        
        # Get all users with their win counts
        user_wins = []
        for user_id, profile in self.user_data.items():
            try:
                user = self.bot.get_user(int(user_id))
                if user:
                    # If server scope, only include users from this server
                    if scope == "server" and interaction.guild:
                        member = interaction.guild.get_member(int(user_id))
                        if not member:
                            continue
                    
                    total_games = profile['wins'] + profile['losses']
                    win_rate = (profile['wins'] / total_games * 100) if total_games > 0 else 0
                    user_wins.append((user, profile['wins'], win_rate))
            except (ValueError, KeyError):
                continue
        
        # Sort by wins (descending)
        user_wins.sort(key=lambda x: x[1], reverse=True)
        
        # Take top 10
        top_users = user_wins[:10]
        
        if not top_users:
            embed = discord.Embed(
                title="🏆 Wins Leaderboard",
                description="No players found with gambling data.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"🏆 Wins Leaderboard ({'Server' if scope == 'server' else 'Global'})",
            color=discord.Color.green()
        )
        
        description_lines = []
        for i, (user, wins, win_rate) in enumerate(top_users):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            description_lines.append(f"{medal} **{user.display_name}** - {wins:,} wins ({win_rate:.1f}%)")
        
        embed.description = "\n".join(description_lines)
        
        # Add user's ranking if not in top 10
        user_rank = None
        for i, (user, wins, win_rate) in enumerate(user_wins):
            if user.id == interaction.user.id:
                user_rank = i + 1
                break
        
        if user_rank and user_rank > 10:
            profile = self.get_user_profile(str(interaction.user.id))
            total_games = profile['wins'] + profile['losses']
            user_win_rate = (profile['wins'] / total_games * 100) if total_games > 0 else 0
            embed.add_field(
                name="Your Ranking",
                value=f"#{user_rank} - {profile['wins']:,} wins ({user_win_rate:.1f}%)",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    # Statistics command
    @app_commands.command(name="stats", description="View detailed gambling statistics")
    @app_commands.describe(user="User to view stats for (optional)")
    async def stats(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View detailed statistics."""
        target_user = user or interaction.user
        profile = self.get_user_profile(str(target_user.id))
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Statistics",
            color=discord.Color.blue()
        )
        
        # Basic stats
        total_games = profile['wins'] + profile['losses']
        win_rate = (profile['wins'] / total_games * 100) if total_games > 0 else 0
        net_profit = profile['total_won'] - profile['total_bet']
        
        embed.add_field(name="💰 Current Cash", value=f"${profile['cash']:,}", inline=True)
        embed.add_field(name="📈 Level", value=f"{profile['level']}", inline=True)
        embed.add_field(name="⭐ XP", value=f"{profile['xp']:,}", inline=True)
        
        embed.add_field(name="🎮 Total Games", value=f"{total_games:,}", inline=True)
        embed.add_field(name="🏆 Wins", value=f"{profile['wins']:,}", inline=True)
        embed.add_field(name="💀 Losses", value=f"{profile['losses']:,}", inline=True)
        
        embed.add_field(name="📊 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.add_field(name="💸 Total Bet", value=f"${profile['total_bet']:,}", inline=True)
        embed.add_field(name="💎 Total Won", value=f"${profile['total_won']:,}", inline=True)
        
        # Net profit with color coding
        profit_color = "🟢" if net_profit >= 0 else "🔴"
        embed.add_field(name=f"{profit_color} Net Profit", value=f"${net_profit:,}", inline=True)
        
        # Calculate rankings
        self.load_user_data()
        
        # Cash ranking
        cash_rankings = sorted(
            [(uid, data['cash']) for uid, data in self.user_data.items()],
            key=lambda x: x[1], reverse=True
        )
        cash_rank = next((i+1 for i, (uid, _) in enumerate(cash_rankings) if uid == str(target_user.id)), "N/A")
        
        # Level ranking
        level_rankings = sorted(
            [(uid, data['level'], data['xp']) for uid, data in self.user_data.items()],
            key=lambda x: (x[1], x[2]), reverse=True
        )
        level_rank = next((i+1 for i, (uid, _, _) in enumerate(level_rankings) if uid == str(target_user.id)), "N/A")
        
        embed.add_field(name="🏆 Cash Rank", value=f"#{cash_rank}", inline=True)
        embed.add_field(name="⭐ Level Rank", value=f"#{level_rank}", inline=True)
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text=f"Statistics for {target_user.display_name}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(LeaderboardCommands(bot))