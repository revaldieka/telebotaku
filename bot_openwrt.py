import os
import re
import logging
import configparser
import subprocess
import asyncio
import json
import time
from pathlib import Path
from telethon import TelegramClient, events, Button
from telethon.tl.custom import Button as TelethonButton
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

# Setup logging with rotation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/revd_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.ini with enhanced validation."""
    config = {
        'api_id': '',
        'api_hash': '',
        'bot_token': '',
        'admin_id': 0,
        'device_name': 'OpenWRT',
        'allowed_users': [],
        'auto_backup': True,
        'notification_enabled': True
    }

    script_dir = Path(__file__).parent
    config_file = script_dir / 'config.ini'
    
    if not config_file.exists():
        logger.error("Config file not found: %s", config_file)
        raise ValueError(f"Config file not found: {config_file}")
    
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        # Telegram section validation
        if 'Telegram' in parser:
            required_fields = ['api_id', 'api_hash', 'bot_token', 'admin_id']
            for field in required_fields:
                if not parser['Telegram'].get(field):
                    raise ValueError(f"{field} is missing in config.ini")
            
            config['api_id'] = parser['Telegram'].get('api_id')
            config['api_hash'] = parser['Telegram'].get('api_hash')
            config['bot_token'] = parser['Telegram'].get('bot_token')
            config['admin_id'] = int(parser['Telegram'].get('admin_id'))
            
            # Parse allowed users (comma-separated)
            allowed_users_str = parser['Telegram'].get('allowed_users', '')
            if allowed_users_str:
                config['allowed_users'] = [int(uid.strip()) for uid in allowed_users_str.split(',') if uid.strip().isdigit()]
                
        # OpenWRT section
        if 'OpenWRT' in parser:
            config['device_name'] = parser['OpenWRT'].get('device_name', config['device_name'])
            config['auto_backup'] = parser['OpenWRT'].getboolean('auto_backup', config['auto_backup'])
            config['notification_enabled'] = parser['OpenWRT'].getboolean('notification_enabled', config['notification_enabled'])
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Admin ID: {config['admin_id']}")
        logger.info(f"Device name: {config['device_name']}")
        logger.info(f"Allowed users: {len(config['allowed_users'])}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

# Load configuration
CONFIG = load_config()

[Rest of the file content remains exactly the same as in the new file content...]