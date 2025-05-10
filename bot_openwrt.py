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
    """Load configuration from config.ini or environment variables."""
    config = {
        # Default values
        'api_id': os.getenv('TELEGRAM_API_ID', '25188016'),
        'api_hash': os.getenv('TELEGRAM_API_HASH', '31d1351ef7b53bc85fd6ec96a9db397a'),
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', '5369509208:AAESs_Eaw087Q2h1dwlxcE_WsQDOfbwmCB0'),
        'admin_id': int(os.getenv('ADMIN_ID', '866930833')),
        'device_name': os.getenv('DEVICE_NAME', 'OpenWRT | REVD.CLOUD')
    }

    # Validate configuration
    if not all([config['api_id'], config['api_hash'], config['bot_token']]):
        logger.error("Missing required configuration values.")
        raise ValueError("Missing required configuration values.")

    # Try to load from config file if it exists
    config_file = Path('config.ini')
    if config_file.exists():
        parser = configparser.ConfigParser()
        parser.read(config_file)
        if 'Telegram' in parser:
            config['api_id'] = parser['Telegram'].get('api_id', config['api_id'])
            config['api_hash'] = parser['Telegram'].get('api_hash', config['api_hash'])
            config['bot_token'] = parser['Telegram'].get('bot_token', config['bot_token'])
            config['admin_id'] = int(parser['Telegram'].get('admin_id', str(config['admin_id'])))
                
        if 'OpenWRT' in parser:
            config['device_name'] = parser['OpenWRT'].get('device_name', config['device_name'])

    logger.info(f"Admin ID: {config['admin_id']}")
    return config

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
        self.user_last_msg = {}  # To track user's last message IDs
        
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
            "system.sh"
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
            
            # Start the client
            await self.client.start(bot_token=self.config['bot_token'])
            
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
            [Button.text("🚀 Speed Test", resize=True), Button.text("📡 Ping Test", resize=True)]
        ]
    
    async def send_message_and_delete_previous(self, event, text, buttons=None, add_keyboard=True):
        """
        Send a new message and delete the previous one if exists.
        Also update the user's last message ID.
        If add_keyboard is True and no buttons provided, adds the main keyboard.
        """
        user_id = event.sender_id
        chat_id = event.chat_id
        
        # Add main keyboard if no buttons provided and add_keyboard is True
        if buttons is None and add_keyboard:
            buttons = self.get_main_keyboard()
        
        # First, try to delete the previous message if exists
        if user_id in self.user_last_msg and self.user_last_msg[user_id]:
            try:
                await self.client.delete_messages(chat_id, self.user_last_msg[user_id])
            except Exception as e:
                logger.error(f"Failed to delete previous message: {str(e)}")
        
        # Send new message with markdown formatting
        try:
            new_msg = await self.client.send_message(
                chat_id, 
                text, 
                buttons=buttons,
                parse_mode='md'  # Use markdown
            )
            # Update last message ID
            self.user_last_msg[user_id] = new_msg.id
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
                self.user_last_msg[user_id] = new_msg.id
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
    
    def copy_script(self, script_name: str) -> bool:
        """Copy a script to /tmp directory."""
        try:
            source_path = self.script_dir / script_name
            if not source_path.exists():
                logger.error(f"Script not found: {source_path}")
                return False
            
            # Use cp command to copy the script
            dest_path = f"/tmp/{script_name}"
            command = f"cp {source_path} {dest_path} && chmod +x {dest_path}"
            self.run_command(command)
            
            logger.info(f"Script {script_name} copied successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to copy script {script_name}: {str(e)}")
            return False
    
    def run_script(self, script_name: str, *args) -> str:
        """Run a script on the OpenWRT device and return its output."""
        try:
            # Ensure the script is copied to /tmp and executable
            if not self.copy_script(script_name):
                return f"Error: Failed to copy {script_name}"
            
            # Build the command with arguments
            command = f"/tmp/{script_name}"
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
            await self.send_message_and_delete_previous(
                event,
                f"🤖 *Welcome to {self.config['device_name']} Bot!*\n\n"
                f"Select an option or use one of these commands:\n"
                f"`/system` - Get system information\n"
                f"`/reboot` - Reboot the device\n"
                f"`/clearram` - Clear RAM cache\n"
                f"`/network` - Get network statistics\n"
                f"`/speedtest` - Run a speed test\n"
                f"`/ping [target]` - Ping a target (default: google.com)\n"
                f"`/help` - Show this help message"
            )
        
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            """Handle /help command."""
            await self.send_message_and_delete_previous(
                event,
                f"🤖 *{self.config['device_name']} Bot Commands:*\n\n"
                f"`/system` - Get system information\n"
                f"`/reboot` - Reboot the device\n"
                f"`/clearram` - Clear RAM cache\n"
                f"`/network` - Get network statistics\n"
                f"`/speedtest` - Run a speed test\n"
                f"`/ping [target]` - Ping a target (default: google.com)\n"
                f"`/help` - Show this help message"
            )
        
        @self.client.on(events.NewMessage(pattern='/system'))
        async def system_handler(event):
            """Handle /system command."""
            await self.send_message_and_delete_previous(event, "🔍 *Getting system information...*", add_keyboard=False)
            result = self.get_overview()
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/reboot'))
        async def reboot_handler(event):
            """Handle /reboot command."""
            # Create confirmation buttons
            confirm_buttons = [
                [Button.inline("✅ Yes", b"reboot_yes"), 
                 Button.inline("❌ No", b"reboot_no")]
            ]
            
            await self.send_message_and_delete_previous(
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
            await self.send_message_and_delete_previous(event, "🔄 *Rebooting the device...*", add_keyboard=False)
            result = self.reboot_device()
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        @self.client.on(events.CallbackQuery(pattern=r"reboot_no"))
        async def reboot_no_handler(event):
            """Handle reboot cancellation."""
            await self.send_message_and_delete_previous(event, "✅ *Reboot cancelled*")
        
        @self.client.on(events.NewMessage(pattern='/clearram'))
        async def clearram_handler(event):
            """Handle /clearram command."""
            await self.send_message_and_delete_previous(event, "🧹 *Clearing RAM cache...*", add_keyboard=False)
            result = self.clear_ram()
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/network'))
        async def network_handler(event):
            """Handle /network command."""
            await self.send_message_and_delete_previous(event, "📊 *Getting network statistics...*", add_keyboard=False)
            result = self.get_network_stats()
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/speedtest'))
        async def speedtest_handler(event):
            """Handle /speedtest command."""
            await self.send_message_and_delete_previous(event, "🚀 *Running speed test (this may take a minute)...*", add_keyboard=False)
            result = self.run_speedtest()
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        @self.client.on(events.NewMessage(pattern='/ping'))
        async def ping_handler(event):
            """Handle /ping command."""
            # Extract target from command if provided
            command_parts = event.text.split()
            target = None
            if len(command_parts) > 1:
                target = command_parts[1]
                await self.send_message_and_delete_previous(event, f"📡 *Running ping test to {target}...*", add_keyboard=False)
            else:
                # Just show a generic message, not mentioning default target
                await self.send_message_and_delete_previous(event, f"📡 *Running ping test...*", add_keyboard=False)
            
            result = self.run_ping(target)
            await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
        
        # Handle button clicks
        @self.client.on(events.NewMessage())
        async def button_handler(event):
            """Handle button clicks."""
            if not isinstance(event.message.message, str):
                return
            
            text = event.message.message
            
            # Process button presses based on text
            if text == "📊 System Info":
                await self.send_message_and_delete_previous(event, "🔍 *Getting system information...*", add_keyboard=False)
                result = self.get_overview()
                await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
            elif text == "🔄 Reboot":
                await reboot_handler(event)
            elif text == "🧹 Clear RAM":
                await self.send_message_and_delete_previous(event, "🧹 *Clearing RAM cache...*", add_keyboard=False)
                result = self.clear_ram()
                await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
            elif text == "🌐 Network Stats":
                await self.send_message_and_delete_previous(event, "📊 *Getting network statistics...*", add_keyboard=False)
                result = self.get_network_stats()
                await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
            elif text == "🚀 Speed Test":
                await self.send_message_and_delete_previous(event, "🚀 *Running speed test (this may take a minute)...*", add_keyboard=False)
                result = self.run_speedtest()
                await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
            elif text == "📡 Ping Test":
                # For button click, use default target without mentioning what it is
                await self.send_message_and_delete_previous(event, "📡 *Running ping test...*", add_keyboard=False)
                result = self.run_ping()
                if result:
                    await self.send_message_and_delete_previous(event, f"```\n{result}\n```")
                else:
                    await self.send_message_and_delete_previous(event, "*Error: Ping test failed. Please try again.*")
    
    async def run(self):
        """Run the bot."""
        # Verify scripts
        if not self.verify_scripts():
            logger.error("Missing required scripts. Please check the plugins directory.")
            print("Error: Missing required scripts. Please check the plugins directory.")
            return False
        
        # Initialize and start the client
        await self.init_client()
        
        print(f"🤖 {self.config['device_name']} bot is running...")
        logger.info(f"{self.config['device_name']} bot started")
        
        try:
            # Keep the bot running
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error(f"Bot runtime error: {str(e)}")
            # Close the client connection if there was an error
            if self.client and self.client.is_connected():
                await self.client.disconnect()
        
        return True

async def main():
    """Main function to run the bot."""
    try:
        # Create plugins directory if it doesn't exist
        plugins_dir = Path(__file__).parent / "plugins"
        if not plugins_dir.exists():
            plugins_dir.mkdir(parents=True)
            logger.info(f"Created plugins directory at {plugins_dir}")
        
        # Copy all required scripts to the plugins directory
        for script_name in ["speedtest.sh", "reboot.sh", "ping.sh", "clear_ram.sh", "vnstat.sh", "system.sh"]:
            source_path = Path(__file__).parent / script_name
            dest_path = plugins_dir / script_name
            
            # Check if source exists
            if source_path.exists():
                # Copy script to plugins directory if not already there
                if not dest_path.exists():
                    with open(source_path, 'r') as src, open(dest_path, 'w') as dst:
                        dst.write(src.read())
                    logger.info(f"Copied {script_name} to plugins directory")
                    # Make the script executable
                    os.chmod(dest_path, 0o755)
            else:
                logger.warning(f"Script {script_name} not found in root directory")
        
        # Create and run the bot
        bot = OpenWRTBot(CONFIG)
        await bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Use asyncio.run() which creates a new event loop and closes it at the end
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Main exception: {str(e)}")
        print(f"Fatal error: {str(e)}")