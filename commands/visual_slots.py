"""
Visual Slot Machine Commands
Contains animated slot machine functionality with image generation.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio
from typing import Optional

# Try to import PIL for image generation
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class VisualSlotsCommands(commands.Cog):
    """Visual slot machine command cog with animations."""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}
        self.load_user_data()
        
        # Slot machine symbols and their values
        self.symbols = {
            '💎': {'value': 500, 'rarity': 1},
            '🍒': {'value': 100, 'rarity': 3},
            '🍊': {'value': 50, 'rarity': 5},
            '🍇': {'value': 25, 'rarity': 8},
            '🔔': {'value': 15, 'rarity': 12},
            '⭐': {'value': 10, 'rarity': 15},
            '🍋': {'value': 5, 'rarity': 20},
            '7️⃣': {'value': 1000, 'rarity': 1}  # Jackpot symbol
        }
        
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
            return True
        return False
    
    def generate_weighted_symbol(self):
        """Generate a symbol based on rarity weights."""
        # Create weighted list
        weighted_symbols = []
        for symbol, data in self.symbols.items():
            weighted_symbols.extend([symbol] * (20 - data['rarity']))  # Higher rarity = lower weight
        
        return random.choice(weighted_symbols)
    
    def calculate_payout(self, symbols, bet_amount):
        """Calculate payout based on symbol combination."""
        # Check for three of a kind
        if symbols[0] == symbols[1] == symbols[2]:
            symbol = symbols[0]
            base_value = self.symbols[symbol]['value']
            return bet_amount * (base_value // 10), f"🎉 JACKPOT! 3x {symbol}"
        
        # Check for two of a kind
        symbol_counts = {}
        for symbol in symbols:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        for symbol, count in symbol_counts.items():
            if count == 2:
                base_value = self.symbols[symbol]['value']
                return bet_amount * (base_value // 20), f"🎊 Two {symbol}s!"
        
        return 0, "No match"
    
    def create_slot_animation_frames(self, final_symbols):
        """Create text-based animation frames for slot spinning."""
        frames = []
        all_symbols = list(self.symbols.keys())
        
        # Create spinning animation (10 frames)
        for frame in range(10):
            if frame < 7:
                # Random symbols while spinning
                frame_symbols = [random.choice(all_symbols) for _ in range(3)]
            else:
                # Gradually reveal final symbols
                frame_symbols = []
                for i in range(3):
                    if frame >= 7 + i:
                        frame_symbols.append(final_symbols[i])
                    else:
                        frame_symbols.append(random.choice(all_symbols))
            
            # Create the slot machine display
            slot_display = f"""
┌─────────────────┐
│  🎰 SLOTS 🎰   │
├─────────────────┤
│  {frame_symbols[0]}   {frame_symbols[1]}   {frame_symbols[2]}  │
└─────────────────┘
            """.strip()
            
            frames.append(slot_display)
        
        return frames

    @app_commands.command(name="vslots", description="Play animated visual slots")
    @app_commands.describe(bet="Amount to bet (use 'max' or 'allin')")
    async def visual_slots(self, interaction: discord.Interaction, bet: str):
        """Visual slot machine with animation."""
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
        
        # Generate final symbols
        final_symbols = [self.generate_weighted_symbol() for _ in range(3)]
        
        # Calculate result
        payout, result_text = self.calculate_payout(final_symbols, bet_amount)
        
        # Create animation frames
        frames = self.create_slot_animation_frames(final_symbols)
        
        # Send initial message
        embed = discord.Embed(
            title="🎰 Visual Slots",
            description="Spinning...",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
        embed.add_field(name="Status", value="🔄 Spinning...", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Animate the slot machine
        for i, frame in enumerate(frames):
            embed = discord.Embed(
                title="🎰 Visual Slots",
                description=f"```\n{frame}\n```",
                color=discord.Color.blue()
            )
            embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
            
            if i < len(frames) - 1:
                embed.add_field(name="Status", value="🔄 Spinning...", inline=True)
            else:
                # Final result
                if payout > 0:
                    embed.add_field(name="Result", value=result_text, inline=True)
                    embed.add_field(name="Payout", value=f"${payout:,}", inline=True)
                    embed.color = discord.Color.green()
                else:
                    embed.add_field(name="Result", value="No match", inline=True)
                    embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
                    embed.color = discord.Color.red()
            
            await asyncio.sleep(0.5)  # Animation delay
            await interaction.edit_original_response(embed=embed)
        
        # Update user data
        profile['total_bet'] += bet_amount
        
        if payout > 0:
            profile['cash'] += payout - bet_amount  # Net profit
            profile['total_won'] += payout
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            # Final winning message
            final_embed = discord.Embed(
                title="🎰 Visual Slots - You Won!",
                description=f"```\n{frames[-1]}\n```",
                color=discord.Color.green()
            )
            final_embed.add_field(name="Result", value=result_text, inline=False)
            final_embed.add_field(name="Bet", value=f"${bet_amount:,}", inline=True)
            final_embed.add_field(name="Payout", value=f"${payout:,}", inline=True)
            final_embed.add_field(name="Profit", value=f"${payout - bet_amount:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            # Final losing message
            final_embed = discord.Embed(
                title="🎰 Visual Slots - Better luck next time!",
                description=f"```\n{frames[-1]}\n```",
                color=discord.Color.red()
            )
            final_embed.add_field(name="Result", value="No match", inline=False)
            final_embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        final_embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        self.save_user_data()
        
        # Wait a moment then show final result
        await asyncio.sleep(1)
        await interaction.edit_original_response(embed=final_embed)

    @app_commands.command(name="slot_info", description="View slot machine symbol values and odds")
    async def slot_info(self, interaction: discord.Interaction):
        """Show slot machine information."""
        embed = discord.Embed(
            title="🎰 Slot Machine Info",
            description="Symbol values and payout information",
            color=discord.Color.blue()
        )
        
        # Sort symbols by value (descending)
        sorted_symbols = sorted(self.symbols.items(), key=lambda x: x[1]['value'], reverse=True)
        
        symbol_info = []
        for symbol, data in sorted_symbols:
            rarity_text = "Ultra Rare" if data['rarity'] <= 2 else "Rare" if data['rarity'] <= 5 else "Common"
            symbol_info.append(f"{symbol} - Value: {data['value']} | {rarity_text}")
        
        embed.add_field(
            name="💎 Symbol Values",
            value="\n".join(symbol_info),
            inline=False
        )
        
        embed.add_field(
            name="🎊 Payout Rules",
            value="**3 of a kind:** Bet × (Symbol Value ÷ 10)\n**2 of a kind:** Bet × (Symbol Value ÷ 20)\n**No match:** Lose bet",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Tips",
            value="• Higher value symbols are rarer\n• 7️⃣ is the jackpot symbol\n• Use 'max' or 'allin' for bigger bets",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(VisualSlotsCommands(bot))