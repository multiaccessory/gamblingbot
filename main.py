#!/usr/bin/env python3
"""
Discord Bot Entry Point
Main script to start the Discord bot with proper error handling and logging.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

from bot import DiscordBot
from utils.logger import setup_logging

def main():
    """Main function to initialize and run the Discord bot."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get bot token from environment
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables!")
        logger.error("Please set your Discord bot token in the .env file or environment variables.")
        sys.exit(1)
    
    # Initialize and run the bot
    try:
        bot = DiscordBot()
        logger.info("Starting Discord bot...")
        asyncio.run(bot.run(bot_token))
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user.")
    except Exception as e:
        logger.error(f"Fatal error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
