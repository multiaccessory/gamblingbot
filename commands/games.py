"""
Additional Gambling Games
Contains more gambling games like blackjack, roulette, and race betting.
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

class GamesCommands(commands.Cog):
    """Additional gambling games cog."""
    
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

    # Blackjack game
    @app_commands.command(name="blackjack", description="Play a game of blackjack")
    @app_commands.describe(
        bet="Amount to bet (use 'max' or 'allin')",
        mode="Game difficulty mode"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="Easy Mode (3:2 odds, shows totals)", value="easy"),
        app_commands.Choice(name="Hard Mode (2:1 odds, no totals)", value="hard")
    ])
    async def blackjack(self, interaction: discord.Interaction, bet: str, mode: str = "easy"):
        """Blackjack gambling game."""
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
        
        # Create deck (6 decks shuffled together)
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = []
        for _ in range(6):  # 6 decks
            for suit in suits:
                for rank in ranks:
                    deck.append(f"{rank}{suit}")
        random.shuffle(deck)
        
        def card_value(card):
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                return 10
            elif rank == 'A':
                return 11  # Will be adjusted later
            else:
                return int(rank)
        
        def hand_value(hand):
            value = sum(card_value(card) for card in hand)
            aces = sum(1 for card in hand if card[:-1] == 'A')
            
            # Adjust for aces
            while value > 21 and aces > 0:
                value -= 10
                aces -= 1
            
            return value
        
        def hand_display(hand, show_totals=True):
            cards_str = ' '.join(hand)
            if show_totals:
                value = hand_value(hand)
                # Show soft total if there's an ace being used as 11
                soft_value = sum(card_value(card) for card in hand)
                if soft_value != value and soft_value <= 21:
                    return f"{cards_str} ({value}/{soft_value})"
                else:
                    return f"{cards_str} ({value})"
            else:
                return cards_str
        
        # Deal initial cards
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]
        
        player_value = hand_value(player_hand)
        dealer_value = hand_value(dealer_hand)
        
        # Check for blackjacks
        player_blackjack = player_value == 21
        dealer_blackjack = dealer_value == 21
        
        embed = discord.Embed(
            title="♠️ Blackjack",
            color=discord.Color.blue()
        )
        
        show_totals = (mode == "easy")
        
        if dealer_blackjack:
            # Dealer blackjack - player loses immediately
            profile['cash'] -= bet_amount
            profile['total_bet'] += bet_amount
            profile['losses'] += 1
            
            embed.add_field(
                name="Your Hand", 
                value=hand_display(player_hand, show_totals), 
                inline=False
            )
            embed.add_field(
                name="Dealer Hand", 
                value=hand_display(dealer_hand, show_totals), 
                inline=False
            )
            embed.add_field(name="Result", value="Dealer Blackjack - You Lose!", inline=False)
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
            embed.color = discord.Color.red()
            
        elif player_blackjack:
            # Player blackjack - wins with 1.5x bonus
            payout_multiplier = 1.5 if mode == "easy" else 2.0
            winnings = int(bet_amount * payout_multiplier)
            
            profile['cash'] += winnings
            profile['total_bet'] += bet_amount
            profile['total_won'] += winnings + bet_amount
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed.add_field(
                name="Your Hand", 
                value=hand_display(player_hand, show_totals), 
                inline=False
            )
            embed.add_field(
                name="Dealer Hand", 
                value=f"{dealer_hand[0]} ?", 
                inline=False
            )
            embed.add_field(name="Result", value="Blackjack! You Win!", inline=False)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
            embed.color = discord.Color.green()
        else:
            # Continue game - player can hit or stand
            embed.add_field(
                name="Your Hand", 
                value=hand_display(player_hand, show_totals), 
                inline=False
            )
            embed.add_field(
                name="Dealer Hand", 
                value=f"{dealer_hand[0]} ?", 
                inline=False
            )
            embed.add_field(
                name="Actions", 
                value="Choose to Hit (get another card) or Stand (keep current hand)", 
                inline=False
            )
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        self.save_user_data()
        
        # If game is still ongoing, add buttons
        if not player_blackjack and not dealer_blackjack:
            view = BlackjackView(self, interaction.user.id, deck, player_hand, dealer_hand, bet_amount, mode)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            await interaction.response.send_message(embed=embed)

    # Roulette game
    @app_commands.command(name="roulette", description="Play roulette")
    @app_commands.describe(
        prediction="What to bet on (e.g., red, black, 0, 1-18, etc.)",
        bet="Amount to bet (use 'max' or 'allin')"
    )
    async def roulette(self, interaction: discord.Interaction, prediction: str, bet: str):
        """Roulette gambling game."""
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
        
        # Roulette wheel (American style with 0 and 00)
        numbers = list(range(0, 37))  # 0-36
        numbers.append('00')
        
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        
        # Spin the wheel
        result = random.choice(numbers)
        
        # Determine color
        if result == 0 or result == '00':
            color = 'green'
        elif result in red_numbers:
            color = 'red'
        else:
            color = 'black'
        
        # Check win conditions and calculate payout
        won = False
        payout_ratio = 0
        
        prediction = prediction.lower().strip()
        
        if prediction == str(result):
            won = True
            payout_ratio = 35  # Single number bet
        elif prediction == 'red' and color == 'red':
            won = True
            payout_ratio = 1
        elif prediction == 'black' and color == 'black':
            won = True
            payout_ratio = 1
        elif prediction == 'green' and color == 'green':
            won = True
            payout_ratio = 17
        elif prediction in ['1sthalf', '1st'] and isinstance(result, int) and 1 <= result <= 18:
            won = True
            payout_ratio = 1
        elif prediction in ['2ndhalf', '2nd'] and isinstance(result, int) and 19 <= result <= 36:
            won = True
            payout_ratio = 1
        elif prediction in ['1st12'] and isinstance(result, int) and 1 <= result <= 12:
            won = True
            payout_ratio = 2
        elif prediction in ['2nd12'] and isinstance(result, int) and 13 <= result <= 24:
            won = True
            payout_ratio = 2
        elif prediction in ['3rd12'] and isinstance(result, int) and 25 <= result <= 36:
            won = True
            payout_ratio = 2
        
        # Update stats
        profile['total_bet'] += bet_amount
        
        if won:
            winnings = bet_amount * payout_ratio
            profile['cash'] += winnings
            profile['total_won'] += winnings + bet_amount
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed = discord.Embed(
                title="🎰 Roulette - You Won!",
                description=f"The ball landed on **{result} {color}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Your Bet", value=prediction.title(), inline=True)
            embed.add_field(name="Payout", value=f"{payout_ratio}:1", inline=True)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title="🎰 Roulette - You Lost!",
                description=f"The ball landed on **{result} {color}**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Your Bet", value=prediction.title(), inline=True)
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=False)
        self.save_user_data()
        
        await interaction.response.send_message(embed=embed)

    # Race betting
    @app_commands.command(name="race", description="Bet on animal races")
    @app_commands.describe(
        racer_type="Type of race",
        prediction="Which racer you think will win (1-12)",
        bet="Amount to bet (use 'max' or 'allin')"
    )
    @app_commands.choices(racer_type=[
        app_commands.Choice(name="🐢 Turtle Race (3 racers, 3:1 odds)", value="turtle"),
        app_commands.Choice(name="🐕 Dog Race (5 racers, 5:1 odds)", value="dog"),
        app_commands.Choice(name="🏇 Horse Race (8 racers, 8:1 odds)", value="horse"),
        app_commands.Choice(name="🦖 Dinosaur Race (12 racers, 12:1 odds)", value="dinosaur")
    ])
    async def race(self, interaction: discord.Interaction, racer_type: str, prediction: int, bet: str):
        """Animal race betting game."""
        profile = self.get_user_profile(str(interaction.user.id))
        bet_amount = self.parse_bet(bet, profile['cash'])
        
        race_config = {
            'turtle': {'emoji': '🐢', 'count': 3, 'odds': 3},
            'dog': {'emoji': '🐕', 'count': 5, 'odds': 5},
            'horse': {'emoji': '🏇', 'count': 8, 'odds': 8},
            'dinosaur': {'emoji': '🦖', 'count': 12, 'odds': 12}
        }
        
        config = race_config[racer_type]
        
        if bet_amount <= 0 or bet_amount > profile['cash']:
            embed = discord.Embed(
                title="❌ Invalid Bet",
                description="You don't have enough cash for that bet!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if prediction < 1 or prediction > config['count']:
            embed = discord.Embed(
                title="❌ Invalid Prediction",
                description=f"Prediction must be between 1 and {config['count']}!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Race simulation
        winner = random.randint(1, config['count'])
        won = prediction == winner
        
        # Update stats
        profile['total_bet'] += bet_amount
        
        # Create race display
        race_display = []
        for i in range(1, config['count'] + 1):
            emoji = config['emoji']
            if i == winner:
                race_display.append(f"{emoji} #{i} 🏆 WINNER!")
            elif i == prediction:
                race_display.append(f"{emoji} #{i} (Your bet)")
            else:
                race_display.append(f"{emoji} #{i}")
        
        if won:
            winnings = bet_amount * config['odds']
            profile['cash'] += winnings
            profile['total_won'] += winnings + bet_amount
            profile['wins'] += 1
            self.add_xp(str(interaction.user.id), 100)
            
            embed = discord.Embed(
                title=f"{config['emoji']} Race - You Won!",
                description=f"Racer #{winner} won the race!",
                color=discord.Color.green()
            )
            embed.add_field(name="Race Results", value='\n'.join(race_display), inline=False)
            embed.add_field(name="Your Bet", value=f"#{prediction}", inline=True)
            embed.add_field(name="Odds", value=f"{config['odds']}:1", inline=True)
            embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
        else:
            profile['cash'] -= bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title=f"{config['emoji']} Race - You Lost!",
                description=f"Racer #{winner} won the race!",
                color=discord.Color.red()
            )
            embed.add_field(name="Race Results", value='\n'.join(race_display), inline=False)
            embed.add_field(name="Your Bet", value=f"#{prediction}", inline=True)
            embed.add_field(name="Lost", value=f"${bet_amount:,}", inline=True)
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=False)
        self.save_user_data()
        
        await interaction.response.send_message(embed=embed)


class BlackjackView(discord.ui.View):
    """Interactive view for blackjack game."""
    
    def __init__(self, cog, user_id, deck, player_hand, dealer_hand, bet_amount, mode):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.deck = deck
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.bet_amount = bet_amount
        self.mode = mode
    
    def hand_value(self, hand):
        """Calculate hand value with ace handling."""
        value = 0
        aces = 0
        for card in hand:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def hand_display(self, hand, show_totals=True):
        """Display hand with optional totals."""
        cards_str = ' '.join(hand)
        if show_totals:
            value = self.hand_value(hand)
            return f"{cards_str} ({value})"
        else:
            return cards_str
    
    @discord.ui.button(label='Hit', style=discord.ButtonStyle.primary, emoji='🃏')
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Hit button - take another card."""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        # Draw a card
        self.player_hand.append(self.deck.pop())
        player_value = self.hand_value(self.player_hand)
        
        if player_value > 21:
            # Bust - player loses
            await self.finish_game(interaction, "bust")
        else:
            # Update the message
            embed = discord.Embed(
                title="♠️ Blackjack",
                color=discord.Color.blue()
            )
            
            show_totals = (self.mode == "easy")
            embed.add_field(
                name="Your Hand", 
                value=self.hand_display(self.player_hand, show_totals), 
                inline=False
            )
            embed.add_field(
                name="Dealer Hand", 
                value=f"{self.dealer_hand[0]} ?", 
                inline=False
            )
            
            if player_value == 21:
                embed.add_field(name="Status", value="21! You must stand.", inline=False)
            else:
                embed.add_field(name="Actions", value="Hit or Stand?", inline=False)
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            if player_value == 21:
                # Auto-stand on 21
                await asyncio.sleep(1)
                await self.finish_game(interaction, "stand", edit=True)
    
    @discord.ui.button(label='Stand', style=discord.ButtonStyle.secondary, emoji='✋')
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stand button - keep current hand."""
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return
        
        await self.finish_game(interaction, "stand")
    
    async def finish_game(self, interaction, action, edit=False):
        """Finish the blackjack game."""
        profile = self.cog.get_user_profile(self.user_id)
        player_value = self.hand_value(self.player_hand)
        
        if action == "bust":
            # Player busted
            profile['cash'] -= self.bet_amount
            profile['total_bet'] += self.bet_amount
            profile['losses'] += 1
            
            embed = discord.Embed(
                title="♠️ Blackjack - Bust!",
                color=discord.Color.red()
            )
            show_totals = (self.mode == "easy")
            embed.add_field(
                name="Your Hand", 
                value=self.hand_display(self.player_hand, show_totals), 
                inline=False
            )
            embed.add_field(name="Result", value="You busted! Dealer wins.", inline=False)
            embed.add_field(name="Lost", value=f"${self.bet_amount:,}", inline=True)
        
        else:
            # Player stood - dealer plays
            dealer_value = self.hand_value(self.dealer_hand)
            
            # Dealer hits until 17 or higher
            while dealer_value < 17:
                self.dealer_hand.append(self.deck.pop())
                dealer_value = self.hand_value(self.dealer_hand)
            
            # Determine winner
            show_totals = (self.mode == "easy")
            
            if dealer_value > 21:
                # Dealer busted - player wins
                payout_multiplier = 1.5 if self.mode == "easy" else 2.0
                winnings = int(self.bet_amount * payout_multiplier)
                
                profile['cash'] += winnings
                profile['total_bet'] += self.bet_amount
                profile['total_won'] += winnings + self.bet_amount
                profile['wins'] += 1
                self.cog.add_xp(self.user_id, 100)
                
                embed = discord.Embed(
                    title="♠️ Blackjack - You Win!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Result", value="Dealer busted! You win!", inline=False)
                embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
                
            elif player_value > dealer_value:
                # Player wins
                payout_multiplier = 1.5 if self.mode == "easy" else 2.0
                winnings = int(self.bet_amount * payout_multiplier)
                
                profile['cash'] += winnings
                profile['total_bet'] += self.bet_amount
                profile['total_won'] += winnings + self.bet_amount
                profile['wins'] += 1
                self.cog.add_xp(self.user_id, 100)
                
                embed = discord.Embed(
                    title="♠️ Blackjack - You Win!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Result", value=f"You win {player_value} vs {dealer_value}!", inline=False)
                embed.add_field(name="Winnings", value=f"${winnings:,}", inline=True)
                
            elif player_value == dealer_value:
                # Push (tie)
                embed = discord.Embed(
                    title="♠️ Blackjack - Push!",
                    color=discord.Color.orange()
                )
                embed.add_field(name="Result", value=f"Push! Both have {player_value}", inline=False)
                embed.add_field(name="Bet Returned", value=f"${self.bet_amount:,}", inline=True)
                
            else:
                # Dealer wins
                profile['cash'] -= self.bet_amount
                profile['total_bet'] += self.bet_amount
                profile['losses'] += 1
                
                embed = discord.Embed(
                    title="♠️ Blackjack - You Lose!",
                    color=discord.Color.red()
                )
                embed.add_field(name="Result", value=f"Dealer wins {dealer_value} vs {player_value}!", inline=False)
                embed.add_field(name="Lost", value=f"${self.bet_amount:,}", inline=True)
            
            embed.add_field(
                name="Your Hand", 
                value=self.hand_display(self.player_hand, show_totals), 
                inline=False
            )
            embed.add_field(
                name="Dealer Hand", 
                value=self.hand_display(self.dealer_hand, show_totals), 
                inline=False
            )
        
        embed.add_field(name="New Balance", value=f"${profile['cash']:,}", inline=True)
        self.cog.save_user_data()
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        if edit:
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)


async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(GamesCommands(bot))