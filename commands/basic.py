"""
Basic Discord Bot Commands
Contains basic slash commands for the Discord bot including ping, info, help, etc.
"""

import discord
from discord.ext import commands
from discord import app_commands
import psutil
import platform
from datetime import datetime, timezone
import time

class BasicCommands(commands.Cog):
    """Basic command cog containing essential bot commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check the bot's latency and response time")
    async def ping(self, interaction: discord.Interaction):
        """Ping command to check bot latency."""
        start_time = time.time()
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )
        
        # Calculate API latency
        api_latency = round(self.bot.latency * 1000, 2)
        
        await interaction.response.send_message(embed=embed)
        
        # Calculate response time
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)
        
        # Update embed with latency info
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Response Time", value=f"{response_time}ms", inline=True)
        
        await interaction.edit_original_response(embed=embed)
    
    @app_commands.command(name="hello", description="Get a friendly greeting from the bot")
    async def hello(self, interaction: discord.Interaction):
        """Simple hello command."""
        user = interaction.user
        
        embed = discord.Embed(
            title="👋 Hello!",
            description=f"Hello {user.mention}! I'm a Discord bot with slash commands support.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Getting Started",
            value="Use `/help` to see all available commands!",
            inline=False
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="info", description="Get detailed information about the bot")
    async def info(self, interaction: discord.Interaction):
        """Bot information command."""
        # Calculate uptime
        uptime = datetime.utcnow() - self.bot.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Get system info
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        cpu_usage = psutil.cpu_percent()
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Bot stats
        embed.add_field(name="Guilds", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        
        # System stats
        embed.add_field(name="Memory Usage", value=f"{memory_usage:.1f} MB", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        
        # Bot info
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="Platform", value=platform.system(), inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Get information about the current server")
    async def serverinfo(self, interaction: discord.Interaction):
        """Server information command."""
        guild = interaction.guild
        
        if not guild:
            await interaction.response.send_message("This command can only be used in a server!", ephemeral=True)
            return
        
        # Count members by status
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Server stats
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:R>", inline=True)
        
        # Member stats
        embed.add_field(name="Total Members", value=guild.member_count, inline=True)
        embed.add_field(name="Humans", value=len([m for m in guild.members if not m.bot]), inline=True)
        embed.add_field(name="Bots", value=len([m for m in guild.members if m.bot]), inline=True)
        
        # Status breakdown
        embed.add_field(name="Online", value=f"🟢 {online}", inline=True)
        embed.add_field(name="Idle", value=f"🟡 {idle}", inline=True)
        embed.add_field(name="DND", value=f"🔴 {dnd}", inline=True)
        
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        
        # Other info
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Get information about a user")
    @app_commands.describe(user="The user to get information about (optional, defaults to you)")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """User information command."""
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # User info
        embed.add_field(name="Username", value=f"{user.name}#{user.discriminator}", inline=True)
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if user.bot else "No", inline=True)
        
        # Dates
        embed.add_field(name="Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
        if hasattr(user, 'joined_at') and user.joined_at:
            embed.add_field(name="Joined Server", value=f"<t:{int(user.joined_at.timestamp())}:R>", inline=True)
        
        # Status and activity
        embed.add_field(name="Status", value=str(user.status).title(), inline=True)
        
        if hasattr(user, 'roles') and len(user.roles) > 1:
            roles = [role.mention for role in user.roles[1:]]  # Exclude @everyone
            if len(roles) > 10:
                roles = roles[:10]
                roles.append(f"... and {len(user.roles) - 11} more")
            embed.add_field(name=f"Roles ({len(user.roles) - 1})", value=" ".join(roles), inline=False)
        
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="help", description="Get help and see all available commands")
    async def help(self, interaction: discord.Interaction):
        """Help command showing all available commands."""
        embed = discord.Embed(
            title="🔧 Bot Commands",
            description="Here are all the available slash commands:",
            color=discord.Color.blue()
        )
        
        # Basic commands
        basic_commands = [
            "`/ping` - Check bot latency and response time",
            "`/hello` - Get a friendly greeting",
            "`/info` - Get detailed bot information",
            "`/serverinfo` - Get current server information",
            "`/userinfo [user]` - Get user information",
            "`/help` - Show this help message"
        ]
        
        # Advanced commands
        advanced_commands = [
            "`/roll` - Roll dice with different types (d4, d6, d8, d10, d12, d20, d100)",
            "`/color` - Get color information with autocomplete",
            "`/settings set` - Set your profile information",
            "`/settings view` - View profile information",
            "`/settings clear` - Clear your profile",
            "`/mod timeout` - Timeout a user (demo)",
            "`/mod warn` - Warn a user (demo)"
        ]
        
        # Gambling commands
        gambling_commands = [
            "`/profile` - View your gambling profile and stats",
            "`/daily` - Claim your daily cash reward",
            "`/work` - Work for money (10min cooldown)",
            "`/coinflip` - Bet on heads or tails (1:1 odds)",
            "`/dice` - Roll dice and bet on result (up to 20:1 odds)",
            "`/slots` - Try your luck at slot machines",
            "`/vslots` - Animated visual slot machine",
            "`/blackjack` - Play blackjack with easy/hard modes",
            "`/roulette` - Bet on roulette (various betting options)",
            "`/race` - Bet on animal races (turtle, dog, horse, dinosaur)"
        ]
        
        # Leaderboard & Stats commands
        leaderboard_commands = [
            "`/leaderboard cash` - Top richest players",
            "`/leaderboard level` - Highest level players", 
            "`/leaderboard wins` - Most wins leaderboard",
            "`/stats [user]` - Detailed gambling statistics",
            "`/slot_info` - Slot machine symbol information"
        ]
        
        # Prefix commands (alternative)
        prefix_commands = [
            "`!money` - Check balance (also works: !cash, !balance)",
            "`!daily` - Claim daily reward",
            "`!work` - Work for money",
            "`!flip <heads/tails> <bet>` - Coinflip gambling",
            "`!dice <type> <prediction> <bet>` - Dice gambling",
            "`!leaderboard <category>` - View leaderboards",
            "`!stats [user]` - View statistics",
            "`!help [command]` - Command help"
        ]
        
        embed.add_field(
            name="📋 Basic Commands",
            value="\n".join(basic_commands),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Advanced Commands",
            value="\n".join(advanced_commands),
            inline=False
        )
        
        embed.add_field(
            name="🎰 Gambling Commands",
            value="\n".join(gambling_commands),
            inline=False
        )
        
        embed.add_field(
            name="📊 Leaderboards & Stats",
            value="\n".join(leaderboard_commands),
            inline=False
        )
        
        embed.add_field(
            name="💬 Prefix Commands",
            value="\n".join(prefix_commands),
            inline=False
        )
        
        embed.add_field(
            name="🔗 Support",
            value="Need help? Contact the bot developer or check the documentation.",
            inline=False
        )
        
        embed.set_footer(text="Use / to see command suggestions while typing!")
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(BasicCommands(bot))
