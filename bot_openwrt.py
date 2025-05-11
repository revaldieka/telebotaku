import os
import re
import logging
import configparser
import subprocess
import asyncio
from pathlib import Path
from telethon import TelegramClient, events, Button
from telethon.tl.custom import Button as TelethonButton
from typing import Dict, Any, Optional, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.ini."""
    config = {
        # Empty defaults - will be filled from config.ini
        'api_id': '',
        'api_hash': '',
        'bot_token': '',
        'admin_id': 0,
        'device_name': 'OpenWRT'
    }

    # Try to load from config file
    script_dir = Path(__file__).parent
    config_file = script_dir / 'config.ini'
    
    if not config_file.exists():
        logger.error("Config file not found: %s", config_file)
        raise ValueError(f"Config file not found: {config_file}")
    
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        if 'Telegram' in parser:
            if not parser['Telegram'].get('api_id'):
                raise ValueError("API ID is missing in config.ini")
            
            if not parser['Telegram'].get('api_hash'):
                raise ValueError("API Hash is missing in config.ini")
            
            if not parser['Telegram'].get('bot_token'):
                raise ValueError("Bot token is missing in config.ini")
            
            if not parser['Telegram'].get('admin_id'):
                raise ValueError("Admin ID is missing in config.ini")
            
            config['api_id'] = parser['Telegram'].get('api_id')
            config['api_hash'] = parser['Telegram'].get('api_hash')
            config['bot_token'] = parser['Telegram'].get('bot_token')
            config['admin_id'] = int(parser['Telegram'].get('admin_id'))
                
        if 'OpenWRT' in parser:
            config['device_name'] = parser['OpenWRT'].get('device_name', config['device_name'])
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Admin ID: {config['admin_id']}")
        logger.info(f"Device name: {config['device_name']}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

# Load configuration
CONFIG = load_config()

class OpenWRTBot:
    """OpenWRT Telegram Bot class for managing and monitoring OpenWRT devices."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the bot with configuration."""
        self.config = config
        self.client = None
        self.admin_id = self.config['admin_id']
        self.script_dir = Path(__file__).parent / "plugins"  # Use plugins directory
        self.me = None  # Store bot user info
        
        # Ensure plugins directory exists
        if not self.script_dir.exists():
            self.script_dir.mkdir(parents=True)
            logger.info(f"Created plugins directory at {self.script_dir}")
            
        # List of required scripts
        self.required_scripts = [
            "speedtest.sh", 
            "reboot.sh", 
            "ping.sh", 
            "clear_ram.sh", 
            "vnstat.sh", 
            "system.sh",
            "userlist.sh",
            "update.sh"  # Added update.sh to required scripts
        ]
        
    async def init_client(self):
        """Initialize the Telegram client."""
        try:
            # Create the client with explicit loop parameter
            self.client = TelegramClient(
                'bot_session', 
                self.config['api_id'], 
                self.config['api_hash'],
                connection_retries=None  # Retry connection indefinitely
            )
            
            # Start the client with bot token from config
            await self.client.start(bot_token=self.config['bot_token'])
            
            # Get bot information
            self.me = await self.client.get_me()
            logger.info(f"Bot initialized as @{self.me.username} (ID: {self.me.id})")
            
            # Set up command handlers
            self.setup_handlers()
            
            logger.info("Telegram client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize client: {str(e)}")
            raise
    
    def get_main_keyboard(self):
        """Return the main keyboard for the bot."""
        return [
            [Button.text("📊 System Info", resize=True), Button.text("🔄 Reboot", resize=True)],
            [Button.text("🧹 Clear RAM", resize=True), Button.text("🌐 Network Stats", resize=True)],
            [Button.text("🚀 Speed Test", resize=True), Button.text("📡 Ping Test", resize=True)],
            [Button.text("👥 User List", resize=True), Button.text("⬆️ Update Bot", resize=True)]  # Added Update Bot button
        ]
    
    async def send_message(self, event, text, buttons=None, add_keyboard=True):
        """
        Send a new message without deleting previous ones.
        If add_keyboard is True and no buttons provided, adds the main keyboard.
        """
        chat_id = event.chat_id
        
        # Add main keyboard if no buttons provided and add_keyboard is True
        if buttons is None and add_keyboard:
            buttons = self.get_main_keyboard()
        
        # Send new message with markdown formatting
        try:
            new_msg = await self.client.send_message(
                chat_id, 
                text, 
                buttons=buttons,
                parse_mode='md'  # Use markdown
            )
            return new_msg
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            # If markdown fails, try without formatting
            try:
                new_msg = await self.client.send_message(
                    chat_id, 
                    text, 
                    buttons=buttons
                )
                return new_msg
            except Exception as e:
                logger.error(f"Error sending plain message: {str(e)}")
                return None
        
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is the admin of the bot."""
        return user_id == self.admin_id
    
    def run_command(self, command: str) -> str:
        """Execute a shell command and return the output."""
        try:
            # Execute command in a shell and capture output
            process = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # Combine stdout and stderr, prioritizing stdout
            result = process.stdout.strip()
            error = process.stderr.strip()
            
            # If there was an error and no standard output, return the error
            if error and not result:
                logger.warning(f"Command error: {error}")
                return f"Error: {error}"
                
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return "Error: Command timed out"
        except Exception as e:
            logger.error(f"Command failed ({command}): {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def run_script(self, script_name: str, *args) -> str:
        """Run a script on the OpenWRT device and return its output."""
        try:
            # Build the script path - using directly from the plugins directory
            script_path = self.script_dir / script_name
            
            # Check if script exists
            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                return f"Error: Script {script_name} not found"
            
            # Make sure it's executable
            os.chmod(script_path, 0o755)
            
            # Build the command with arguments
            command = f"{script_path}"
            if args:
                command += " " + " ".join(str(arg) for arg in args)
            
            # Execute the script
            return self.run_command(command)
        except Exception as e:
            logger.error(f"Failed to run script {script_name}: {str(e)}")
            return f"Error running {script_name}: {str(e)}"

    def get_overview(self) -> str:
        """Get system overview from OpenWRT device."""
        try:
            return self.run_script("system.sh")
        except Exception as e:
            logger.error(f"Error getting overview: {str(e)}")
            return f"Failed to get device overview: {str(e)}"

    def reboot_device(self) -> str:
        """Reboot the OpenWRT device."""
        try:
            return self.run_script("reboot.sh")
        except Exception as e:
            logger.error(f"Reboot failed: {str(e)}")
            return f"❌ Reboot failed: {str(e)}"

    def clear_ram(self) -> str:
        """Clear RAM cache on the OpenWRT device."""
        try:
            return self.run_script("clear_ram.sh")
        except Exception as e:
            logger.error(f"Clear RAM failed: {str(e)}")
            return f"❌ Failed to clear RAM: {str(e)}"
    
    def run_speedtest(self) -> str:
        """Run internet speed test."""
        try:
            return self.run_script("speedtest.sh")
        except Exception as e:
            logger.error(f"Speed test failed: {str(e)}")
            return f"❌ Speed test failed: {str(e)}"
    
    def run_ping(self, target: str = None) -> str:
        """Run ping test to a specified target."""
        try:
            if target:
                return self.run_script("ping.sh", target)
            else:
                return self.run_script("ping.sh")
        except Exception as e:
            logger.error(f"Ping test failed: {str(e)}")
            return f"❌ Ping test failed: {str(e)}"
    
    def get_network_stats(self) -> str:
        """Get network statistics using vnstat."""
        try:
            return self.run_script("vnstat.sh")
        except Exception as e:
            logger.error(f"Network stats failed: {str(e)}")
            return f"❌ Failed to get network statistics: {str(e)}"
    
    def get_user_list(self) -> str:
        """Get list of connected users."""
        try:
            return self.run_script("userlist.sh")
        except Exception as e:
            logger.error(f"User list failed: {str(e)}")
            return f"❌ Failed to get user list: {str(e)}"
    
    def update_bot(self) -> str:
        """Update bot from GitHub repository."""
        try:
            return self.run_script("update.sh")
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            return f"❌ Update failed: {str(e)}"
    
    def verify_scripts(self) -> bool:
        """Verify that all required scripts are in the plugins directory."""
        missing_scripts = []
        for script in self.required_scripts:
            if not (self.script_dir / script).exists():
                missing_scripts.append(script)
        
        if missing_scripts:
            logger.error(f"Missing scripts: {', '.join(missing_scripts)}")
            return False
        return True
    
    def setup_handlers(self):
        """Set up message handlers for the bot."""
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            """Handle /start command."""
            await self.send_message(
                event,
                f"🤖 *Welcome to {self.config['device_name']} Bot!*\n\n"
                f"Select an option or use one of these commands:\n"
                f"`/system` - Get system information\n"
                f"`/reboot` - Reboot the device\n"
                f"`/clearram` - Clear RAM cache\n"
                f"`/network` - Get network statistics\n"
                f"`/speedtest` - Run a speed test\n"
                f"`/ping [target]` - Ping a target (default: google.com)\n"
                f"`/userlist` - List connected users\n"
                f"`/update` - Update bot from GitHub\n"
                f"`/help` - Show this help message"
            )
        
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            """Handle /help command."""
            await self.send_message(
                event,
                f"🤖 *{self.config['device_name']} Bot Commands:*\n\n"
                f"`/system` - Get system information\n"
                f"`/reboot` - Reboot the device\n"
                f"`/clearram` - Clear RAM cache\n"
                f"`/network` - Get network statistics\n"
                f"`/speedtest` - Run a speed test\n"
                f"`/ping [target]` - Ping a target (default: google.com)\n"
                f"`/userlist` - List connected users\n"
                f"`/update` - Update bot from GitHub\n"
                f"`/help` - Show this help message"
            )
        
        @self.client.on(events.NewMessage(pattern='/system'))
        async def system_handler(event):
            """Handle /system command."""
            await self.send_message(event, "🔍 *Getting system information...*", add_keyboard=False)
            result = self.get_overview()
            await self.send_message(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/reboot'))
        async def reboot_handler(event):
            """Handle /reboot command."""
            # Create confirmation buttons
            confirm_buttons = [
                [Button.inline("✅ Yes", b"reboot_yes"), 
                 Button.inline("❌ No", b"reboot_no")]
            ]
            
            await self.send_message(
                event, 
                "⚠️ *Are you sure you want to reboot the device?*\n\n"
                "This will disconnect the device for 1-2 minutes.",
                buttons=confirm_buttons,
                add_keyboard=False
            )
        
        @self.client.on(events.CallbackQuery(pattern=r"reboot_yes"))
        async def reboot_yes_handler(event):
            """Handle reboot confirmation."""
            user_id = event.sender_id
            # Log who initiated the reboot
            logger.info(f"User {user_id} confirmed reboot")
            await self.send_message(event, "🔄 *Rebooting the device...*", add_keyboard=False)
            result = self.reboot_device()
            await self.send_message(event, f"```\n{result}\n```")
        
        @self.client.on(events.CallbackQuery(pattern=r"reboot_no"))
        async def reboot_no_handler(event):
            """Handle reboot cancellation."""
            await self.send_message(event, "✅ *Reboot cancelled*")

        @self.client.on(events.NewMessage(pattern='/update'))
        async def update_handler(event):
            """Handle /update command."""
            # Only allow admin to update
            if not self.is_admin(event.sender_id):
                await self.send_message(event, "⛔ *Only admin can update the bot*")
                return
                
            # Create confirmation buttons
            confirm_buttons = [
                [Button.inline("✅ Yes", b"update_yes"), 
                 Button.inline("❌ No", b"update_no")]
            ]
            
            await self.send_message(
                event, 
                "⚠️ *Are you sure you want to update the bot?*\n\n"
                "This will download the latest version from GitHub.",
                buttons=confirm_buttons,
                add_keyboard=False
            )

        @self.client.on(events.CallbackQuery(pattern=r"update_yes"))
        async def update_yes_handler(event):
            """Handle update confirmation."""
            user_id = event.sender_id
            # Only allow admin to update
            if not self.is_admin(user_id):
                await self.send_message(event, "⛔ *Only admin can update the bot*")
                return
                
            # Log who initiated the update
            logger.info(f"User {user_id} confirmed update")
            await self.send_message(event, "🔄 *Updating the bot...*", add_keyboard=False)
            result = self.update_bot()
            await self.send_message(event, f"```\n{result}\n```")

        @self.client.on(events.CallbackQuery(pattern=r"update_no"))
        async def update_no_handler(event):
            """Handle update cancellation."""
            await self.send_message(event, "✅ *Update cancelled*")
        
        @self.client.on(events.NewMessage(pattern='/clearram'))
        async def clearram_handler(event):
            """Handle /clearram command."""
            await self.send_message(event, "🧹 *Clearing RAM cache...*", add_keyboard=False)
            result = self.clear_ram()
            await self.send_message(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/network'))
        async def network_handler(event):
            """Handle /network command."""
            await self.send_message(event, "📊 *Getting network statistics...*", add_keyboard=False)
            result = self.get_network_stats()
            await self.send_message(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/speedtest'))
        async def speedtest_handler(event):
            """Handle /speedtest command."""
            await self.send_message(event, "🚀 *Running speed test (this may take a minute)...*", add_keyboard=False)
            result = self.run_speedtest()
            await self.send_message(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/ping'))
        async def ping_handler(event):
            """Handle /ping command."""
            # Extract target from command if provided
            command_parts = event.text.split()
            target = None
            if len(command_parts) > 1:
                target = command_parts[1]
                await self.send_message(event, f"📡 *Running ping test to {target}...*", add_keyboard=False)
            else:
                # Just show a generic message, not mentioning default target
                await self.send_message(event, f"📡 *Running ping test...*", add_keyboard=False)
            
            result = self.run_ping(target)
            await self.send_message(event, f"```\n{result}\n```")

        @self.client.on(events.NewMessage(pattern='/userlist'))
        async def userlist_handler(event):
            """Handle /userlist command."""
            await self.send_message(event, "👥 *Getting user list...*", add_keyboard=False)
            result = self.get_user_list()
            await self.send_message(event, f"```\n{result}\n```")
        
        # Handle button clicks
        @self.client.on(events.NewMessage())
        async def button_handler(event):
            """Handle button clicks."""
            if not isinstance(event.message.message, str):
                return
            
            text = event.message.message
            
            # Process button presses based on text
            if text == "📊 System Info":
                await self.send_message(event, "🔍 *Getting system information...*", add_keyboard=False)
                result = self.get_overview()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "🔄 Reboot":
                await reboot_handler(event)
            elif text == "🧹 Clear RAM":
                await self.send_message(event, "🧹 *Clearing RAM cache...*", add_keyboard=False)
                result = self.clear_ram()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "🌐 Network Stats":
                await self.send_message(event, "📊 *Getting network statistics...*", add_keyboard=False)
                result = self.get_network_stats()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "🚀 Speed Test":
                await self.send_message(event, "🚀 *Running speed test (this may take a minute)...*", add_keyboard=False)
                result = self.run_speedtest()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "📡 Ping Test":
                await self.send_message(event, "📡 *Running ping test...*", add_keyboard=False)
                result = self.run_ping()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "👥 User List":
                await self.send_message(event, "👥 *Getting user list...*", add_keyboard=False)
                result = self.get_user_list()
                await self.send_message(event, f"```\n{result}\n```")
            elif text == "⬆️ Update Bot":
                # Only allow admin to update
                if not self.is_admin(event.sender_id):
                    await self.send_message(event, "⛔ *Only admin can update the bot*")
                    return
                await update_handler(event)
        
        # Admin verification
        @self.client.on(events.NewMessage())
        async def admin_check_handler(event):
            """Verify if the user is an admin."""
            # Skip messages from the bot itself
            if event.sender_id == self.me.id:  # Fixed: Use self.me.id instead of self.client.user_id
                return
                
            # If message is from non-admin, check if it's a command
            if not self.is_admin(event.sender_id):
                # Check if the message is a command that requires admin access
                if event.message.message.startswith('/update') or event.message.message == "⬆️ Update Bot":
                    await self.send_message(event, "⛔ *Only admin can access this command*")
                    return
                    
                # For all other commands, allow access for any user

async def main():
    """Main entry point for the bot."""
    try:
        # Create the bot instance
        bot = OpenWRTBot(CONFIG)
        
        # Verify all required scripts are present
        if not bot.verify_scripts():
            logger.warning("Some required scripts are missing. Bot functionality will be limited.")
        
        # Initialize the client
        await bot.init_client()
        
        logger.info(f"Bot started for {CONFIG['device_name']}")
        
        # Keep the bot running
        await bot.client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the bot
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        loop.close()
