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
from telethon.errors import FloodWaitError
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
                
        # OpenWRT section
        if 'OpenWRT' in parser:
            config['device_name'] = parser['OpenWRT'].get('device_name', config['device_name'])
            config['auto_backup'] = parser['OpenWRT'].getboolean('auto_backup', config['auto_backup'])
            config['notification_enabled'] = parser['OpenWRT'].getboolean('notification_enabled', config['notification_enabled'])
        
        logger.info(f"Configuration loaded successfully")
        logger.info(f"Admin ID: {config['admin_id']}")
        logger.info(f"Device name: {config['device_name']}")
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

# Load configuration
CONFIG = load_config()

# Bot statistics
bot_stats = {
    'start_time': datetime.now(),
    'commands_executed': 0,
    'errors_count': 0,
    'last_command': None,
    'command_history': []
}

# Rate limiting and flood control
flood_control = {
    'unauthorized_users': {},  # Track unauthorized users
    'flood_wait_until': 0,     # Global flood wait timestamp
    'last_response_time': 0    # Last response timestamp
}

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == CONFIG['admin_id']

def should_respond_to_unauthorized(user_id: int) -> bool:
    """Check if we should respond to unauthorized user (rate limiting)."""
    current_time = time.time()
    
    # Check if user exists in tracking
    if user_id not in flood_control['unauthorized_users']:
        flood_control['unauthorized_users'][user_id] = {
            'last_response': 0,
            'message_count': 0,
            'blocked_until': 0
        }
    
    user_data = flood_control['unauthorized_users'][user_id]
    
    # If user is temporarily blocked
    if current_time < user_data['blocked_until']:
        return False
    
    # If last response was less than 5 minutes ago, don't respond
    if current_time - user_data['last_response'] < 300:  # 5 minutes
        user_data['message_count'] += 1
        
        # If user sent more than 3 messages, block for 1 hour
        if user_data['message_count'] > 3:
            user_data['blocked_until'] = current_time + 3600  # 1 hour
            logger.warning(f"User {user_id} blocked for 1 hour due to spam")
        
        return False
    
    # Reset message count and allow response
    user_data['message_count'] = 1
    user_data['last_response'] = current_time
    return True

def log_command(user_id: int, username: str, command: str):
    """Log command execution."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'user_id': user_id,
        'username': username,
        'command': command
    }
    
    bot_stats['commands_executed'] += 1
    bot_stats['last_command'] = log_entry
    bot_stats['command_history'].append(log_entry)
    
    # Keep only last 50 commands
    if len(bot_stats['command_history']) > 50:
        bot_stats['command_history'] = bot_stats['command_history'][-50:]
    
    logger.info(f"Command executed: {command} by {username} ({user_id})")

async def safe_respond(event, message, buttons=None, **kwargs):
    """Safely respond to messages with comprehensive flood control."""
    try:
        current_time = time.time()
        
        # Check global flood wait
        if current_time < flood_control['flood_wait_until']:
            logger.warning(f"Skipping response due to global flood wait until {flood_control['flood_wait_until']}")
            return None
        
        # Rate limit responses (minimum 1 second between responses)
        if current_time - flood_control['last_response_time'] < 1:
            await asyncio.sleep(1)
        
        flood_control['last_response_time'] = time.time()
        
        if buttons:
            return await event.respond(message, buttons=buttons, **kwargs)
        else:
            return await event.respond(message, **kwargs)
            
    except FloodWaitError as e:
        # Handle flood wait error
        wait_time = e.seconds
        flood_control['flood_wait_until'] = current_time + wait_time
        logger.error(f"FloodWaitError: Must wait {wait_time} seconds")
        
        # Don't try to send another message during flood wait
        return None
        
    except Exception as e:
        logger.error(f"Error in safe_respond: {str(e)}")
        bot_stats['errors_count'] += 1
        return None

async def run_shell_command(command: str, timeout: int = 30) -> str:
    """Execute shell command with timeout and error handling."""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        
        if process.returncode == 0:
            return stdout.decode('utf-8', errors='ignore').strip()
        else:
            error_msg = stderr.decode('utf-8', errors='ignore').strip()
            logger.error(f"Command failed: {command}, Error: {error_msg}")
            return f"❌ Command failed: {error_msg}"
            
    except asyncio.TimeoutError:
        logger.error(f"Command timeout: {command}")
        return f"⏰ Command timed out after {timeout} seconds"
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        bot_stats['errors_count'] += 1
        return f"❌ Error executing command: {str(e)}"

def get_device_info():
    """Get device information for display."""
    try:
        # Get hostname
        hostname = subprocess.check_output("uci get system.@system[0].hostname 2>/dev/null || echo 'Unknown'", shell=True).decode().strip()
        
        # Get OpenWRT version
        try:
            with open('/etc/openwrt_release', 'r') as f:
                content = f.read()
                version_line = [line for line in content.split('\n') if 'DISTRIB_DESCRIPTION' in line]
                if version_line:
                    version = version_line[0].split("'")[1]
                else:
                    version = "Unknown"
        except:
            version = "Unknown"
        
        # Get uptime
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                if days > 0:
                    uptime = f"{days}d {hours:02d}:{minutes:02d}"
                else:
                    uptime = f"{hours:02d}:{minutes:02d}"
        except:
            uptime = "Unknown"
        
        return {
            'hostname': hostname,
            'version': version,
            'uptime': uptime
        }
    except:
        return {
            'hostname': 'Unknown',
            'version': 'Unknown', 
            'uptime': 'Unknown'
        }

def get_main_keyboard():
    """Generate main keyboard with all available commands."""
    keyboard = [
        [Button.inline("📊 System Info", b"system"), Button.inline("🔄 Reboot", b"reboot")],
        [Button.inline("🧹 Clear RAM", b"clearram"), Button.inline("🌐 Network Stats", b"network")],
        [Button.inline("🚀 Speed Test", b"speedtest"), Button.inline("📡 Ping Test", b"ping")],
        [Button.inline("📶 WiFi Info", b"wifi"), Button.inline("🔥 Firewall", b"firewall")],
        [Button.inline("👥 User List", b"userlist"), Button.inline("💾 Backup", b"backup")],
        [Button.inline("📈 Bot Stats", b"stats"), Button.inline("⬆️ Update Bot", b"update")],
        [Button.inline("📜 History", b"history"), Button.inline("🗑️ Uninstall", b"uninstall")],
        [Button.inline("ℹ️ Help", b"help")]
    ]
    return keyboard

def get_confirmation_keyboard(action_type):
    """Generate confirmation keyboard for destructive actions."""
    if action_type == "reboot":
        return [
            [Button.inline("✅ Yes, Reboot", b"confirm_reboot"), Button.inline("❌ Cancel", b"cancel_action")]
        ]
    elif action_type == "update":
        return [
            [Button.inline("✅ Yes, Update", b"confirm_update"), Button.inline("❌ Cancel", b"cancel_action")]
        ]
    elif action_type == "uninstall":
        return [
            [Button.inline("🗑️ Delete All", b"uninstall_all")],
            [Button.inline("💾 Keep Config", b"uninstall_keep")],
            [Button.inline("❌ Cancel", b"cancel_action")]
        ]
    return []

# Initialize Telegram client
client = TelegramClient('bot_session', CONFIG['api_id'], CONFIG['api_hash'])

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        # Check if we should respond to this unauthorized user
        if not should_respond_to_unauthorized(user_id):
            logger.info(f"Rate limiting unauthorized user {username} ({user_id})")
            return
        
        await safe_respond(event, 
            "❌ **Access Denied**\n\n"
            "This bot is restricted to the administrator only.\n"
            "Contact the device owner for access.\n\n"
            "🌐 **REVD.CLOUD** - Professional OpenWRT Solutions"
        )
        logger.warning(f"Unauthorized access attempt by {username} ({user_id})")
        return
    
    log_command(user_id, username, "/start")
    
    device_info = get_device_info()
    
    welcome_message = f"""
🤖 **Welcome to {CONFIG['device_name']} Bot!**

✅ **Bot Status**: Online and Ready
🔧 **Device**: {device_info['hostname']}
📊 **Version**: {device_info['version']}
⏱️ **Uptime**: {device_info['uptime']}
👤 **Admin**: {username}
🆔 **Your ID**: `{user_id}`

**🌐 REVD.CLOUD Professional Services:**
• Custom OpenWRT bot development
• Network infrastructure consulting
• Remote device management solutions
• 24/7 technical support & monitoring

**🚀 Quick Actions:**
Use the buttons below for instant access to all features!

**📞 Contact & Support:**
• Website: https://revd.cloud
• Telegram: @ValltzID
• Instagram: @revd.cloud
• Email: support@revd.cloud

**⚡ Powered by REVD.CLOUD Technology**
"""
    
    keyboard = get_main_keyboard()
    await safe_respond(event, welcome_message, buttons=keyboard)

@client.on(events.NewMessage(pattern='/menu'))
async def menu_handler(event):
    """Handle /menu command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/menu")
    
    device_info = get_device_info()
    
    menu_text = f"""
🤖 **{CONFIG['device_name']} Management Bot**

📡 **Device Information:**
• **Hostname:** {device_info['hostname']}
• **Version:** {device_info['version']}
• **Uptime:** {device_info['uptime']}

🔧 **Available Commands:**

**📊 System Management:**
• System information & status
• Restart device (with confirmation)
• Clear RAM cache
• Create system backup

**🌐 Network Monitoring:**
• Network statistics (vnstat)
• Internet speed test
• Ping test (default: google.com)
• WiFi information & clients
• Firewall status & rules
• Connected devices list

**📈 Bot Management:**
• Bot statistics & performance
• Show this menu
• Detailed help information
• Update bot from GitHub
• Remove bot from system
• Command execution history

**🌐 REVD.CLOUD Professional Services:**
• **Website:** https://revd.cloud
• **Telegram:** @ValltzID
• **Instagram:** @revd.cloud
• **Support:** Professional OpenWRT solutions

**🚀 Bot Version:** Enhanced Edition v2.1
**⚡ Powered by:** REVD.CLOUD Technology
"""
    
    keyboard = get_main_keyboard()
    await safe_respond(event, menu_text, buttons=keyboard)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/help")
    
    device_info = get_device_info()
    
    help_text = f"""
🤖 **{CONFIG['device_name']} Bot - Complete Guide**

📡 **Device:** {device_info['hostname']} | **Version:** {device_info['version']}

**📊 System Commands:**
• **System Info** - Complete system information (CPU, RAM, temperature, network)
• **Reboot** - Restart device with safety confirmation
• **Clear RAM** - Clear system RAM cache for better performance
• **Backup** - Create compressed system backup

**🌐 Network Commands:**
• **Network Stats** - Network usage statistics via vnstat
• **Speed Test** - Internet speed test (download/upload/ping)
• **Ping Test** - Network connectivity test (default: google.com)
• **WiFi Info** - WiFi networks, clients, and signal information
• **Firewall** - Firewall status, rules, and port forwards
• **User List** - List of connected devices with details

**📈 Bot Commands:**
• **Bot Stats** - Bot performance and usage statistics
• **Help** - This detailed help information
• **Menu** - Show main menu with device information

**🔐 Admin Commands:**
• **Update Bot** - Update bot to latest version from GitHub
• **Uninstall** - Safely remove bot with backup options
• **History** - View command execution history

**💡 Usage Tips:**
• Use buttons for quick access to all features
• Some operations may take 30-60 seconds
• Bot logs all activities for security
• All commands require admin authorization

**🛡️ Security Features:**
• Admin-only authorization system
• Command logging and audit trail
• Session management and timeout protection
• Unauthorized access monitoring
• Rate limiting and flood protection

**🌐 REVD.CLOUD Professional Services:**

**🔧 What We Offer:**
• Custom OpenWRT bot development
• Network infrastructure consulting
• Remote device management solutions
• 24/7 technical support and monitoring
• Enterprise deployment services

**📞 Contact Information:**
• **Website:** https://revd.cloud
• **Telegram:** @ValltzID
• **Instagram:** @revd.cloud
• **Email:** support@revd.cloud

**🚀 Why Choose REVD.CLOUD:**
• Expert OpenWRT developers
• Proven track record in network solutions
• Custom solutions for enterprise clients
• Competitive pricing and fast delivery
• Professional support and maintenance

**📋 Our Portfolio:**
• Telegram bot automation systems
• Network monitoring solutions
• Custom firmware development
• IoT device management platforms
• Enterprise network consulting

**🎯 Get Professional Support:**
Contact us for custom bot features, enterprise deployments, or technical consulting services.

**⚡ Powered by REVD.CLOUD Technology**
"""
    
    keyboard = get_main_keyboard()
    await safe_respond(event, help_text, buttons=keyboard)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle button callbacks."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    data = event.data.decode('utf-8')
    
    if not is_admin(user_id):
        await event.answer("❌ Access denied.", alert=True)
        return
    
    log_command(user_id, username, f"button:{data}")
    
    try:
        await event.answer("⏳ Processing...")
        
        if data == "system":
            await handle_system_command(event)
        elif data == "reboot":
            await handle_reboot_command(event)
        elif data == "confirm_reboot":
            await handle_reboot_confirm(event)
        elif data == "clearram":
            await handle_clearram_command(event)
        elif data == "network":
            await handle_network_command(event)
        elif data == "speedtest":
            await handle_speedtest_command(event)
        elif data == "ping":
            await handle_ping_command(event)
        elif data == "wifi":
            await handle_wifi_command(event)
        elif data == "firewall":
            await handle_firewall_command(event)
        elif data == "userlist":
            await handle_userlist_command(event)
        elif data == "backup":
            await handle_backup_command(event)
        elif data == "stats":
            await handle_stats_command(event)
        elif data == "help":
            await help_handler(event)
        elif data == "update":
            await handle_update_command(event)
        elif data == "confirm_update":
            await handle_update_confirm(event)
        elif data == "uninstall":
            await handle_uninstall_command(event)
        elif data == "uninstall_all":
            await handle_uninstall_all(event)
        elif data == "uninstall_keep":
            await handle_uninstall_keep(event)
        elif data == "history":
            await handle_history_command(event)
        elif data == "cancel_action":
            await handle_cancel_action(event)
        else:
            await safe_respond(event, "❌ Unknown command.")
            
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        bot_stats['errors_count'] += 1
        await safe_respond(event, f"❌ Error processing command: {str(e)}")

async def handle_system_command(event):
    """Handle system info command."""
    processing_msg = await safe_respond(event, "⏳ **Getting system information...**\n\nPlease wait while I collect system data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/system.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_reboot_command(event):
    """Handle reboot command with confirmation."""
    device_info = get_device_info()
    
    confirm_msg = f"""
⚠️ **Reboot Confirmation Required**

**Device:** {device_info['hostname']}
**Current Uptime:** {device_info['uptime']}

**Warning:** This will restart your OpenWRT device!
• Device will be offline for 1-2 minutes
• All active connections will be dropped
• Services will restart automatically

**Choose an option below:**
"""
    
    keyboard = get_confirmation_keyboard("reboot")
    await safe_respond(event, confirm_msg, buttons=keyboard)

async def handle_reboot_confirm(event):
    """Handle reboot confirmation."""
    device_info = get_device_info()
    
    await safe_respond(event, f"🔄 **Rebooting {device_info['hostname']}**\n\nDevice is restarting... Please wait 1-2 minutes before reconnecting.")
    
    # Execute reboot
    await run_shell_command("sh /root/REVDBOT/plugins/reboot.sh")

async def handle_clearram_command(event):
    """Handle clear RAM command."""
    processing_msg = await safe_respond(event, "🧹 **Clearing RAM cache...**\n\nOptimizing memory usage...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/clear_ram.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_network_command(event):
    """Handle network stats command."""
    processing_msg = await safe_respond(event, "📊 **Collecting network statistics...**\n\nAnalyzing network usage data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/vnstat.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_speedtest_command(event):
    """Handle speedtest command."""
    processing_msg = await safe_respond(event, "🚀 **Running Internet Speed Test**\n\nTesting download/upload speeds...\nThis may take 30-60 seconds.")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/speedtest.sh", timeout=120)
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_ping_command(event, target="google.com"):
    """Handle ping command."""
    processing_msg = await safe_respond(event, f"📡 **Testing connection to {target}**\n\nSending ping packets...")
    
    result = await run_shell_command(f"sh /root/REVDBOT/plugins/ping.sh {target}")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_wifi_command(event):
    """Handle WiFi info command."""
    processing_msg = await safe_respond(event, "📶 **Scanning WiFi information...**\n\nGathering wireless network data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/wifi.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_firewall_command(event):
    """Handle firewall status command."""
    processing_msg = await safe_respond(event, "🔥 **Checking firewall status...**\n\nAnalyzing security rules...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/firewall.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_userlist_command(event):
    """Handle user list command."""
    processing_msg = await safe_respond(event, "👥 **Scanning connected devices...**\n\nListing active network clients...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/userlist.sh")
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_backup_command(event):
    """Handle backup command."""
    processing_msg = await safe_respond(event, "💾 **Creating System Backup**\n\nBacking up configuration and settings...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/backup.sh", timeout=60)
    
    keyboard = get_main_keyboard()
    await safe_respond(event, f"```\n{result}\n```", buttons=keyboard)

async def handle_stats_command(event):
    """Handle bot statistics command."""
    uptime = datetime.now() - bot_stats['start_time']
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    device_info = get_device_info()
    
    stats_text = f"""
📈 **Bot Performance Statistics**

**🤖 Bot Information:**
• **Uptime:** {uptime_str}
• **Version:** Enhanced Edition v2.1
• **Commands Executed:** {bot_stats['commands_executed']}
• **Errors Encountered:** {bot_stats['errors_count']}

**📡 Device Information:**
• **Device:** {device_info['hostname']}
• **System:** {device_info['version']}
• **Uptime:** {device_info['uptime']}

**📋 Recent Activity:**
"""
    
    if bot_stats['last_command']:
        last_cmd = bot_stats['last_command']
        stats_text += f"• **Last Command:** `{last_cmd['command']}`\n"
        stats_text += f"• **Executed by:** {last_cmd['username']}\n"
        stats_text += f"• **Time:** {last_cmd['timestamp']}\n"
    else:
        stats_text += "• No commands executed yet\n"
    
    stats_text += f"""
**🛡️ Security Status:**
• **Unauthorized Attempts:** {len(flood_control['unauthorized_users'])}
• **Flood Protection:** Active
• **Rate Limiting:** Enabled

**🌐 REVD.CLOUD Services:**
• Professional OpenWRT solutions
• Custom bot development
• Network consulting services
• 24/7 technical support

**📞 Contact:** @ValltzID | https://revd.cloud
"""
    
    keyboard = get_main_keyboard()
    await safe_respond(event, stats_text, buttons=keyboard)

async def handle_update_command(event):
    """Handle update command."""
    confirm_msg = f"""
⬆️ **Bot Update Confirmation**

**Current Version:** Enhanced Edition v2.1
**Source:** GitHub Repository (revaldieka/telebotaku)

**Update Process:**
• Download latest version from GitHub
• Backup current configuration
• Update bot files and plugins
• Restart bot service automatically

**Warning:** Bot will be offline for 1-2 minutes during update.

**Choose an option below:**
"""
    
    keyboard = get_confirmation_keyboard("update")
    await safe_respond(event, confirm_msg, buttons=keyboard)

async def handle_update_confirm(event):
    """Handle update confirmation."""
    update_msg = await safe_respond(event, "⬆️ **Starting Bot Update**\n\nDownloading latest version from GitHub...\nPlease wait...")
    
    # Execute update
    result = await run_shell_command("sh /root/REVDBOT/plugins/update.sh", timeout=120)
    await safe_respond(event, f"```\n{result}\n```")

async def handle_uninstall_command(event):
    """Handle uninstall command."""
    device_info = get_device_info()
    
    confirm_msg = f"""
🗑️ **Bot Uninstall Confirmation**

**Device:** {device_info['hostname']}
**Bot Version:** Enhanced Edition v2.1

⚠️ **WARNING:** This will completely remove the bot from your system!

**Uninstall Options:**
• **Delete All** - Remove everything
• **Keep Config** - Save configuration for future reinstall
• **Cancel** - Abort uninstall

**What will be removed:**
• Bot service and startup scripts
• All bot files and plugins
• Log files and session data
• Service configuration

**Note:** Configuration backup will be saved to `/etc/revd_backup/` if you choose "Keep Config" option.
"""
    
    keyboard = get_confirmation_keyboard("uninstall")
    await safe_respond(event, confirm_msg, buttons=keyboard)

async def handle_uninstall_all(event):
    """Handle complete uninstall."""
    uninstall_msg = await safe_respond(event, "🗑️ **Complete Bot Removal**\n\nRemoving all bot files and configuration...\nGoodbye! 👋")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh n")
    await safe_respond(event, f"```\n{result}\n```")

async def handle_uninstall_keep(event):
    """Handle uninstall with config backup."""
    uninstall_msg = await safe_respond(event, "💾 **Uninstalling with Configuration Backup**\n\nSaving configuration and removing bot...\nYou can reinstall later with saved settings!")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh y")
    await safe_respond(event, f"```\n{result}\n```")

async def handle_history_command(event):
    """Handle command history."""
    if not bot_stats['command_history']:
        keyboard = get_main_keyboard()
        await safe_respond(event, "📜 **Command History**\n\nNo commands have been executed yet.", buttons=keyboard)
        return
    
    history_text = "📜 **Command Execution History** (Last 10)\n\n"
    
    # Show last 10 commands
    recent_commands = bot_stats['command_history'][-10:]
    for i, cmd in enumerate(reversed(recent_commands), 1):
        history_text += f"**{i}.** `{cmd['command']}`\n"
        history_text += f"   👤 **User:** {cmd['username']}\n"
        history_text += f"   🕒 **Time:** {cmd['timestamp']}\n\n"
    
    history_text += f"**📊 Total Commands Executed:** {bot_stats['commands_executed']}\n"
    history_text += f"**⚡ Bot Uptime:** {str(datetime.now() - bot_stats['start_time']).split('.')[0]}"
    
    keyboard = get_main_keyboard()
    await safe_respond(event, history_text, buttons=keyboard)

async def handle_cancel_action(event):
    """Handle action cancellation."""
    keyboard = get_main_keyboard()
    await safe_respond(event, "❌ **Action Cancelled**\n\nOperation has been cancelled.", buttons=keyboard)

# Text command handlers for direct commands
@client.on(events.NewMessage(pattern='/system'))
async def system_text_command(event):
    """Handle /system text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/system")
    await handle_system_command(event)

@client.on(events.NewMessage(pattern=r'/ping(?:\s+(.+))?'))
async def ping_text_command(event):
    """Handle /ping text command with optional target."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    target = event.pattern_match.group(1) or "google.com"
    log_command(user_id, username, f"/ping {target}")
    await handle_ping_command(event, target)

@client.on(events.NewMessage(pattern='/reboot'))
async def reboot_text_command(event):
    """Handle /reboot text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/reboot")
    await handle_reboot_command(event)

@client.on(events.NewMessage(pattern='/clearram'))
async def clearram_text_command(event):
    """Handle /clearram text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/clearram")
    await handle_clearram_command(event)

@client.on(events.NewMessage(pattern='/network'))
async def network_text_command(event):
    """Handle /network text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/network")
    await handle_network_command(event)

@client.on(events.NewMessage(pattern='/speedtest'))
async def speedtest_text_command(event):
    """Handle /speedtest text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/speedtest")
    await handle_speedtest_command(event)

@client.on(events.NewMessage(pattern='/wifi'))
async def wifi_text_command(event):
    """Handle /wifi text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/wifi")
    await handle_wifi_command(event)

@client.on(events.NewMessage(pattern='/firewall'))
async def firewall_text_command(event):
    """Handle /firewall text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/firewall")
    await handle_firewall_command(event)

@client.on(events.NewMessage(pattern='/userlist'))
async def userlist_text_command(event):
    """Handle /userlist text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/userlist")
    await handle_userlist_command(event)

@client.on(events.NewMessage(pattern='/backup'))
async def backup_text_command(event):
    """Handle /backup text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/backup")
    await handle_backup_command(event)

@client.on(events.NewMessage(pattern='/stats'))
async def stats_text_command(event):
    """Handle /stats text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ Access denied.")
        return
    
    log_command(user_id, username, "/stats")
    await handle_stats_command(event)

@client.on(events.NewMessage(pattern='/update'))
async def update_text_command(event):
    """Handle /update text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ **Admin Access Required**\n\nThis command is restricted to the administrator only.")
        return
    
    log_command(user_id, username, "/update")
    await handle_update_command(event)

@client.on(events.NewMessage(pattern='/uninstall'))
async def uninstall_text_command(event):
    """Handle /uninstall text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ **Admin Access Required**\n\nThis command is restricted to the administrator only.")
        return
    
    log_command(user_id, username, "/uninstall")
    await handle_uninstall_command(event)

@client.on(events.NewMessage(pattern='/history'))
async def history_text_command(event):
    """Handle /history text command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        if should_respond_to_unauthorized(user_id):
            await safe_respond(event, "❌ **Admin Access Required**\n\nThis command is restricted to the administrator only.")
        return
    
    log_command(user_id, username, "/history")
    await handle_history_command(event)

async def send_startup_notification():
    """Send startup notification to admin."""
    if not CONFIG['notification_enabled']:
        return
    
    try:
        device_info = get_device_info()
        
        startup_message = f"""
🚀 **Bot Started Successfully**

✅ **Status:** Online and Ready
🔧 **Device:** {device_info['hostname']}
📊 **Version:** {device_info['version']}
⏰ **Started:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **Bot Version:** Enhanced Edition v2.1

**📡 Device Information:**
• **Hostname:** {device_info['hostname']}
• **System:** {device_info['version']}
• **Uptime:** {device_info['uptime']}

**⚙️ Configuration:**
• **Admin ID:** {CONFIG['admin_id']}
• **Auto Backup:** {'✅' if CONFIG['auto_backup'] else '❌'}
• **Notifications:** {'✅' if CONFIG['notification_enabled'] else '❌'}

**🛡️ Security Features:**
• **Flood Protection:** Active
• **Rate Limiting:** Enabled
• **Admin-Only Access:** Enforced

**🌐 REVD.CLOUD Professional Services:**
Professional OpenWRT management solutions now available!
• Custom bot development
• Network infrastructure consulting  
• 24/7 technical support
• Enterprise deployment services

**📞 Contact:** @ValltzID | https://revd.cloud

**🚀 Bot is ready to receive commands!**
Type `/start` to begin or use the buttons for quick access.
"""
        
        keyboard = get_main_keyboard()
        await client.send_message(CONFIG['admin_id'], startup_message, buttons=keyboard)
        logger.info("Startup notification sent to admin")
        
    except Exception as e:
        logger.error(f"Failed to send startup notification: {str(e)}")

async def main():
    """Main function to start the bot."""
    try:
        logger.info("Starting Telegram Bot...")
        logger.info(f"Device: {CONFIG['device_name']}")
        logger.info(f"Admin ID: {CONFIG['admin_id']}")
        
        # Start the client
        await client.start(bot_token=CONFIG['bot_token'])
        
        # Send startup notification
        await send_startup_notification()
        
        logger.info("Bot started successfully!")
        logger.info("Press Ctrl+C to stop the bot")
        
        # Keep the bot running
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {str(e)}")
        bot_stats['errors_count'] += 1
        raise
    finally:
        logger.info("Bot shutting down...")

if __name__ == '__main__':
    asyncio.run(main())