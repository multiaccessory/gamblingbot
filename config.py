"""
Bot Configuration
Contains configuration settings and constants for the Discord bot.
"""

import os
from typing import List

class BotConfig:
    """Configuration class for bot settings."""
    
    # Bot settings
    COMMAND_PREFIX: str = "!"
    CASE_INSENSITIVE: bool = True
    
    # Bot status settings
    DEFAULT_STATUS: str = "online"
    DEFAULT_ACTIVITY_TYPE: str = "watching"
    DEFAULT_ACTIVITY_NAME: str = "for /help"
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    
    # API settings
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))
    
    # Feature flags
    ENABLE_LOGGING: bool = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    ENABLE_ERROR_REPORTING: bool = os.getenv("ENABLE_ERROR_REPORTING", "true").lower() == "true"
    
    # Command settings
    COMMAND_COOLDOWN: int = int(os.getenv("COMMAND_COOLDOWN", "3"))  # seconds
    MAX_COMMAND_LENGTH: int = int(os.getenv("MAX_COMMAND_LENGTH", "2000"))
    
    @classmethod
    def get_required_env_vars(cls) -> List[str]:
        """Get list of required environment variables."""
        return [
            "DISCORD_BOT_TOKEN"
        ]
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that all required configuration is present."""
        missing_vars = []
        
        for var in cls.get_required_env_vars():
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True

# Bot metadata
BOT_VERSION = "1.0.0"
BOT_AUTHOR = "Discord Bot Developer"
BOT_DESCRIPTION = "A Python Discord bot with slash commands functionality"
