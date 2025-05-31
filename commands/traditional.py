"""
Traditional Prefix Commands
Contains traditional Discord commands with prefix support for backward compatibility.
"""

import discord
from discord.ext import commands
import json
import os
import random
from datetime import datetime, timedelta

class TraditionalCommands(commands.Cog):
    """Traditional prefix command cog."""
    
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
    
    def parse_bet(self, bet_str: str, user_cash: int) -> int:
        """Parse bet string and return amount."""
        if not bet_str:
            return 0
            
        bet_str = str(bet_str).lower().strip()
        
        if bet_str in ['max', 'm']:
            return user_cash
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

    # Traditional prefix commands
    @commands.command(name='money', aliases=['cash', 'balance', 'bal'])
    async def money(self, ctx, user: discord.Member = None):
        """Check money balance."""
        target_user = user or ctx.author
        profile = self.get_user_profile(str(target_user.id))
        
        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Balance",
            color=discord.Color.gold()
        )
        embed.add_field(name="Cash", value=f"${profile['cash']:,}", inline=True)
        embed.add_field(name="Level", value=profile['level'], inline=True)
        embed.add_field(name="XP", value=f"{profile['xp']:,}", inline=True)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='daily')
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hour cooldown
    async def daily(self, ctx):
        """Claim daily reward."""
        profile = self.get_user_profile(str(ctx.author.id))
        
        base_reward = 1000
        level_bonus = profile['level'] * 100
        total_reward = base_reward + level_bonus
        
        profile['cash'] += total_reward
        self.save_user_data()
        
        embed = discord.Embed(
            title="🎁 Daily Reward Claimed!",
            description=f"You received **${total_reward:,}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='work')
    @commands.cooldown(1, 600, commands.BucketType.user)  # 10 minute cooldown
    async def work(self, ctx):
        """Work for money."""
        profile = self.get_user_profile(str(ctx.author.id))
        
        base_reward = random.randint(100, 500)
        level_bonus = profile['level'] * 10
        total_reward = base_reward + level_bonus
        
        profile['cash'] += total_reward
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
        
        await ctx.send(embed=embed)

    @commands.command(name='flip', aliases=['coinflip', 'cf'])
    async def coinflip(self, ctx, choice: str = None, bet: str = "100"):
        """Flip a coin."""
        if not choice or choice.lower() not in ['heads', 'tails', 'h', 't']:
            await ctx.send("Please specify `heads` or `tails` (or `h`/`t`)")
            return
        
        profile = self.get_user_profile(str(ctx.author.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            await ctx.send("Invalid bet amount or insufficient funds!")
            return
        
        # Normalize choice
        prediction = 'heads' if choice.lower() in ['heads', 'h'] else 'tails'
        result = random.choice(['heads', 'tails'])
        won = prediction == result
        
        profile['total_bet'] += bet_amount
        
        if won:
            winnings = bet_amount
            profile['cash'] += winnings
            profile['total_won'] += winnings + bet_amount
            profile['wins'] += 1
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Won!",
                description=f"The coin landed on **{result}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title="🪙 Coinflip - You Lost!",
                description=f"The coin landed on **{result}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        self.save_user_data()
        
        await ctx.send(embed=embed)

    @commands.command(name='dice', aliases=['roll'])
    async def dice_roll(self, ctx, dice_type: str = "d6", prediction: int = 1, bet: str = "100"):
        """Roll dice and bet on result."""
        # Parse dice type
        if dice_type.startswith('d'):
            try:
                sides = int(dice_type[1:])
            except ValueError:
                sides = 6
        else:
            try:
                sides = int(dice_type)
            except ValueError:
                sides = 6
        
        if sides not in [4, 6, 8, 10, 12, 20]:
            await ctx.send("Valid dice types: d4, d6, d8, d10, d12, d20")
            return
        
        profile = self.get_user_profile(str(ctx.author.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            await ctx.send("Invalid bet amount or insufficient funds!")
            return
        
        if prediction < 1 or prediction > sides:
            await ctx.send(f"Prediction must be between 1 and {sides}!")
            return
        
        result = random.randint(1, sides)
        won = prediction == result
        
        profile['total_bet'] += bet_amount
        
        if won:
            winnings = bet_amount * sides
            profile['cash'] += winnings
            profile['total_won'] += winnings + bet_amount
            profile['wins'] += 1
            
            embed = discord.Embed(
                title=f"🎲 d{sides} - You Won!",
                description=f"The dice rolled **{result}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title=f"🎲 d{sides} - You Lost!",
                description=f"The dice rolled **{result}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        self.save_user_data()
        
        await ctx.send(embed=embed)

    @commands.command(name='leaderboard', aliases=['top', 'lb'])
    async def leaderboard(self, ctx, category: str = "cash"):
        """Show leaderboards."""
        self.load_user_data()
        
        if category.lower() in ['cash', 'money', 'balance']:
            # Cash leaderboard
            user_cash = []
            for user_id, profile in self.user_data.items():
                try:
                    user = self.bot.get_user(int(user_id))
                    if user and ctx.guild and ctx.guild.get_member(int(user_id)):
                        user_cash.append((user, profile['cash']))
                except (ValueError, KeyError):
                    continue
            
            user_cash.sort(key=lambda x: x[1], reverse=True)
            top_users = user_cash[:10]
            
            embed = discord.Embed(
                title="💰 Cash Leaderboard",
                color=discord.Color.gold()
            )
            
            description_lines = []
            for i, (user, cash) in enumerate(top_users):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                description_lines.append(f"{medal} **{user.display_name}** - ${cash:,}")
            
            embed.description = "\n".join(description_lines) if description_lines else "No players found."
            
        elif category.lower() in ['level', 'levels', 'xp']:
            # Level leaderboard
            user_levels = []
            for user_id, profile in self.user_data.items():
                try:
                    user = self.bot.get_user(int(user_id))
                    if user and ctx.guild and ctx.guild.get_member(int(user_id)):
                        user_levels.append((user, profile['level'], profile['xp']))
                except (ValueError, KeyError):
                    continue
            
            user_levels.sort(key=lambda x: (x[1], x[2]), reverse=True)
            top_users = user_levels[:10]
            
            embed = discord.Embed(
                title="⭐ Level Leaderboard",
                color=discord.Color.purple()
            )
            
            description_lines = []
            for i, (user, level, xp) in enumerate(top_users):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                description_lines.append(f"{medal} **{user.display_name}** - Level {level} ({xp:,} XP)")
            
            embed.description = "\n".join(description_lines) if description_lines else "No players found."
            
        else:
            await ctx.send("Available categories: `cash`, `level`")
            return
        
        await ctx.send(embed=embed)

    @commands.command(name='stats', aliases=['profile'])
    async def stats(self, ctx, user: discord.Member = None):
        """View detailed statistics."""
        target_user = user or ctx.author
        profile = self.get_user_profile(str(target_user.id))
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Statistics",
            color=discord.Color.blue()
        )
        
        total_games = profile['wins'] + profile['losses']
        win_rate = (profile['wins'] / total_games * 100) if total_games > 0 else 0
        net_profit = profile['total_won'] - profile['total_bet']
        
        embed.add_field(name="💰 Cash", value=f"${profile['cash']:,}", inline=True)
        embed.add_field(name="📈 Level", value=f"{profile['level']}", inline=True)
        embed.add_field(name="⭐ XP", value=f"{profile['xp']:,}", inline=True)
        
        embed.add_field(name="🎮 Games", value=f"{total_games:,}", inline=True)
        embed.add_field(name="🏆 Wins", value=f"{profile['wins']:,}", inline=True)
        embed.add_field(name="📊 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        embed.add_field(name="💸 Total Bet", value=f"${profile['total_bet']:,}", inline=True)
        embed.add_field(name="💎 Total Won", value=f"${profile['total_won']:,}", inline=True)
        embed.add_field(name="📈 Net Profit", value=f"${net_profit:,}", inline=True)
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx, command_name: str = None):
        """Show help information."""
        if command_name:
            # Show specific command help
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Help: {command.name}",
                    description=command.help or "No description available.",
                    color=discord.Color.blue()
                )
                if command.aliases:
                    embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
                
                embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.name} {command.signature}`", inline=False)
            else:
                embed = discord.Embed(
                    title="Command Not Found",
                    description=f"No command named '{command_name}' found.",
                    color=discord.Color.red()
                )
        else:
            # Show general help
            embed = discord.Embed(
                title="🎰 Bot Commands",
                description="Available prefix commands:",
                color=discord.Color.blue()
            )
            
            commands_list = [
                f"`{ctx.prefix}money` - Check your balance",
                f"`{ctx.prefix}daily` - Claim daily reward",
                f"`{ctx.prefix}work` - Work for money",
                f"`{ctx.prefix}flip <heads/tails> <bet>` - Coinflip gambling",
                f"`{ctx.prefix}dice <type> <prediction> <bet>` - Dice gambling",
                f"`{ctx.prefix}leaderboard <category>` - View leaderboards",
                f"`{ctx.prefix}stats [user]` - View statistics",
                f"`{ctx.prefix}help [command]` - Show this help"
            ]
            
            embed.add_field(
                name="💰 Economy & Gambling",
                value="\n".join(commands_list),
                inline=False
            )
            
            embed.add_field(
                name="💡 Tips",
                value="• Use `/` for modern slash commands\n• Bet amounts support k, m, g suffixes\n• Use 'max' or 'allin' for maximum bets",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(TraditionalCommands(bot))