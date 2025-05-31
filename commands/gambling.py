"""
Gambling Bot Commands
Contains gambling games, economy system, and user management functionality.
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
import random
import json
import os
import asyncio
from datetime import datetime, timedelta

class GamblingCommands(commands.Cog):
    """Gambling command cog with economy and games."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}  # In-memory storage for demo
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
    
    def parse_bet(self, bet_str: str, user_cash: int, max_bet: int = None) -> int:
        """Parse bet string and return amount."""
        bet_str = bet_str.lower().strip()
        
        if bet_str in ['max', 'm']:
            return max_bet or user_cash
        elif bet_str in ['allin', 'a', 'all']:
            return user_cash
        
        # Handle suffixes
        multipliers = {
            'k': 1000,
            'm': 1000000,
            'g': 1000000000,
            't': 1000000000000
        }
        
        for suffix, multiplier in multipliers.items():
            if bet_str.endswith(suffix):
                try:
                    return int(float(bet_str[:-1]) * multiplier)
                except ValueError:
                    return 0
        
        try:
            return int(float(bet_str))
        except ValueError:
            return 0
    
    def add_xp(self, user_id: str, amount: int):
        """Add XP and handle level ups."""
        profile = self.get_user_profile(user_id)
        profile['xp'] += amount
        
        # Level up calculation (1000 XP per level)
        new_level = profile['xp'] // 1000
        if new_level > profile['level']:
            profile['level'] = new_level
            return True  # Level up occurred
        return False

    # Profile command
    @app_commands.command(name="profile", description="View your gambling profile")
    @app_commands.describe(user="User to view profile for (optional)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """View user profile."""
        target_user = user or interaction.user
        profile = self.get_user_profile(str(target_user.id))
        
        embed = discord.Embed(
            title=f"🎰 {target_user.display_name}'s Profile",
            color=discord.Color.gold()
        )
        
        # Basic stats
        embed.add_field(name="💰 Cash", value=f"${profile['cash']:,}", inline=True)
        embed.add_field(name="📈 Level", value=profile['level'], inline=True)
        embed.add_field(name="⭐ XP", value=f"{profile['xp']:,}", inline=True)
        
        # Win/Loss ratio
        total_games = profile['wins'] + profile['losses']
        win_rate = (profile['wins'] / total_games * 100) if total_games > 0 else 0
        embed.add_field(name="🏆 Wins", value=profile['wins'], inline=True)
        embed.add_field(name="💀 Losses", value=profile['losses'], inline=True)
        embed.add_field(name="📊 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        # Money stats
        embed.add_field(name="💸 Total Bet", value=f"${profile['total_bet']:,}", inline=True)
        embed.add_field(name="💎 Total Won", value=f"${profile['total_won']:,}", inline=True)
        net_profit = profile['total_won'] - profile['total_bet']
        embed.add_field(name="📈 Net Profit", value=f"${net_profit:,}", inline=True)
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text=f"Player since joining the bot")
        
        await interaction.response.send_message(embed=embed)

    # Daily command
    @app_commands.command(name="daily", description="Claim your daily reward")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily reward."""
        profile = self.get_user_profile(str(interaction.user.id))
        now = datetime.now()
        
        if profile['last_daily']:
            last_daily = datetime.fromisoformat(profile['last_daily'])
            if now.date() == last_daily.date():
                next_daily = last_daily.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                time_left = next_daily - now
                hours, remainder = divmod(time_left.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                embed = discord.Embed(
                    title="⏰ Daily Already Claimed",
                    description=f"Come back in {hours}h {minutes}m for your next daily reward!",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Calculate daily reward (base 1000 + level bonus)
        base_reward = 1000
        level_bonus = profile['level'] * 100
        total_reward = base_reward + level_bonus
        
        profile['cash'] += total_reward
        profile['last_daily'] = now.isoformat()
        self.save_user_data()
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **${total_reward:,}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="Base Reward", value=f"${base_reward:,}", inline=True)
        embed.add_field(name="Level Bonus", value=f"${level_bonus:,}", inline=True)
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Work command
    @app_commands.command(name="work", description="Work for some cash")
    async def work(self, interaction: discord.Interaction):
        """Work for money."""
        profile = self.get_user_profile(str(interaction.user.id))
        now = datetime.now()
        
        if profile['last_work']:
            last_work = datetime.fromisoformat(profile['last_work'])
            if (now - last_work).total_seconds() < 600:  # 10 minutes
                time_left = 600 - (now - last_work).total_seconds()
                minutes, seconds = divmod(time_left, 60)
                
                embed = discord.Embed(
                    title="⏰ Still Working",
                    description=f"You can work again in {int(minutes)}m {int(seconds)}s",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Random work reward
        base_reward = random.randint(100, 500)
        level_bonus = profile['level'] * 10
        total_reward = base_reward + level_bonus
        
        profile['cash'] += total_reward
        profile['last_work'] = now.isoformat()
        self.save_user_data()
        
        work_messages = [
            "You worked as a casino dealer",
            "You counted cards at a blackjack table",
            "You delivered poker chips",
            "You cleaned slot machines",
            "You worked as a croupier"
        ]
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"{random.choice(work_messages)} and earned **${total_reward:,}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        
        await interaction.response.send_message(embed=embed)

    # Coinflip game
    @app_commands.command(name="coinflip", description="Flip a coin and bet on the result")
    @app_commands.describe(
        prediction="Choose heads or tails",
        bet="Amount to bet (use 'max' or 'allin')"
    )
    @app_commands.choices(prediction=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Coin flip gambling game."""
        profile = self.get_user_profile(str(interaction.user.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="You don't have enough cash for that bet!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Flip the coin
        result = random.choice(['heads', 'tails'])
        won = prediction.lower() == result
        
        # Update stats
        profile['total_bet'] += bet_amount
        if won:
            winnings = bet_amount  # 1:1 odds
            profile['cash'] += winnings
            profile['total_won'] += winnings
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Won!",
                description=f"The coin landed on **{result}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Your Prediction", value=prediction.title(), inline=True)
            embed.add_field(name="Result", value=result.title(), inline=True)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Lost!",
                description=f"The coin landed on **{result}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Your Prediction", value=prediction.title(), inline=True)
            embed.add_field(name="Result", value=result.title(), inline=True)
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=False)
        self.save_user_data()
        
        await interaction.response.send_message(embed=embed)

    # Dice roll game
    @app_commands.command(name="dice", description="Roll dice and bet on the result")
    @app_commands.describe(
        dice_type="Type of dice to roll",
        prediction="What number will it land on?",
        bet="Amount to bet (use 'max' or 'allin')"
    )
    @app_commands.choices(dice_type=[
        app_commands.Choice(name="4-sided (d4)", value="4"),
        app_commands.Choice(name="6-sided (d6)", value="6"),
        app_commands.Choice(name="8-sided (d8)", value="8"),
        app_commands.Choice(name="10-sided (d10)", value="10"),
        app_commands.Choice(name="12-sided (d12)", value="12"),
        app_commands.Choice(name="20-sided (d20)", value="20")
    ])
    async def dice(self, interaction: discord.Interaction, dice_type: str, prediction: int, bet: str):
        """Dice roll gambling game."""
        profile = self.get_user_profile(str(interaction.user.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        sides = int(dice_type)
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="You don't have enough cash for that bet!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if prediction < 1 or prediction > sides:
            embed = discord.Embed(
                title="❌ Invalid Prediction",
                description=f"Prediction must be between 1 and {sides}!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Roll the dice
        result = random.randint(1, sides)
        won = prediction == result
        
        # Update stats
        profile['total_bet'] += bet_amount
        if won:
            winnings = bet_amount * sides  # Payout = dice_max:1
            profile['cash'] += winnings
            profile['total_won'] += winnings
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed = discord.Embed(
                title=f"🎲 d{sides} Dice - You Won!",
                description=f"The dice rolled **{result}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Your Prediction", value=prediction, inline=True)
            embed.add_field(name="Result", value=result, inline=True)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title=f"🎲 d{sides} Dice - You Lost!",
                description=f"The dice rolled **{result}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Your Prediction", value=prediction, inline=True)
            embed.add_field(name="Result", value=result, inline=True)
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=False)
        self.save_user_data()
        
        await interaction.response.send_message(embed=embed)

    # Slots game
    @app_commands.command(name="slots", description="Try your luck at the slot machine")
    @app_commands.describe(bet="Amount to bet (use 'max' or 'allin')")
    async def slots(self, interaction: discord.Interaction, bet: str):
        """Slot machine game."""
        profile = self.get_user_profile(str(interaction.user.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="You don't have enough cash for that bet!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Slot symbols and their payouts
        symbols = {
            '💎': {'weight': 1, 'payout_3': 500, 'payout_2': 25},
            '🍒': {'weight': 2, 'payout_3': 25, 'payout_2': 10},
            '🍊': {'weight': 3, 'payout_3': 5, 'payout_2': 3},
            '🍇': {'weight': 4, 'payout_3': 3, 'payout_2': 2},
            '🔔': {'weight': 5, 'payout_3': 2, 'payout_2': 1},
            '⭐': {'weight': 6, 'payout_3': 1, 'payout_2': 1}
        }
        
        # Create weighted symbol list
        weighted_symbols = []
        for symbol, data in symbols.items():
            weighted_symbols.extend([symbol] * data['weight'])
        
        # Spin the slots
        results = [random.choice(weighted_symbols) for _ in range(3)]
        
        # Calculate winnings
        winnings = 0
        win_description = ""
        
        # Check for 3 of a kind first
        if results[0] == results[1] == results[2]:
            symbol = results[0]
            payout_ratio = symbols[symbol]['payout_3']
            winnings = bet_amount * payout_ratio
            win_description = f"3x {symbol} - {payout_ratio}:1 payout!"
        # Check for 2 of a kind
        elif results[0] == results[1] or results[1] == results[2] or results[0] == results[2]:
            # Find the matching symbol
            if results[0] == results[1]:
                symbol = results[0]
            elif results[1] == results[2]:
                symbol = results[1]
            else:
                symbol = results[0]
            
            payout_ratio = symbols[symbol]['payout_2']
            winnings = bet_amount * payout_ratio
            win_description = f"2x {symbol} - {payout_ratio}:1 payout!"
        
        # Update stats
        profile['total_bet'] += bet_amount
        
        if winnings > 0:
            profile['cash'] += winnings - bet_amount  # Net winnings
            profile['total_won'] += winnings
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed = discord.Embed(
                title="🎰 Slots - You Won!",
                description=f"**{' '.join(results)}**\n\n{win_description}",
                color=discord.Color.green()
            )
            embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
            embed.add_field(name="Profit", value=f"${winnings - bet_amount:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title="🎰 Slots - No Win",
                description=f"**{' '.join(results)}**\n\nBetter luck next time!",
                color=discord.Color.red()
            )
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=False)
        self.save_user_data()
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(GamblingCommands(bot))