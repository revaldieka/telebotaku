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

# Bot statistics
bot_stats = {
    'start_time': datetime.now(),
    'commands_executed': 0,
    'errors_count': 0,
    'last_command': None,
    'command_history': [],
    'user_activity': {}
}

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    return user_id == CONFIG['admin_id'] or user_id in CONFIG['allowed_users']

def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == CONFIG['admin_id']

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
    
    # Update user activity
    if user_id not in bot_stats['user_activity']:
        bot_stats['user_activity'][user_id] = {'username': username, 'count': 0}
    bot_stats['user_activity'][user_id]['count'] += 1
    
    logger.info(f"Command executed: {command} by {username} ({user_id})")

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

def get_main_keyboard():
    """Generate main keyboard with all available commands."""
    keyboard = [
        [Button.inline("📊 System Info", b"system"), Button.inline("🔄 Reboot", b"reboot")],
        [Button.inline("🧹 Clear RAM", b"clearram"), Button.inline("🌐 Network Stats", b"network")],
        [Button.inline("🚀 Speed Test", b"speedtest"), Button.inline("📡 Ping Test", b"ping")],
        [Button.inline("📶 WiFi Info", b"wifi"), Button.inline("🔥 Firewall", b"firewall")],
        [Button.inline("👥 User List", b"userlist"), Button.inline("💾 Backup", b"backup")],
        [Button.inline("📈 Bot Stats", b"stats"), Button.inline("⬆️ Update Bot", b"update")],
        [Button.inline("🗑️ Uninstall Bot", b"uninstall"), Button.inline("ℹ️ Help", b"help")]
    ]
    return keyboard

def get_admin_keyboard():
    """Generate admin-only keyboard."""
    keyboard = [
        [Button.inline("📊 System Info", b"system"), Button.inline("🔄 Reboot", b"reboot")],
        [Button.inline("🧹 Clear RAM", b"clearram"), Button.inline("🌐 Network Stats", b"network")],
        [Button.inline("🚀 Speed Test", b"speedtest"), Button.inline("📡 Ping Test", b"ping")],
        [Button.inline("📶 WiFi Info", b"wifi"), Button.inline("🔥 Firewall", b"firewall")],
        [Button.inline("👥 User List", b"userlist"), Button.inline("💾 Backup", b"backup")],
        [Button.inline("📈 Bot Stats", b"stats"), Button.inline("⬆️ Update Bot", b"update")],
        [Button.inline("📜 Command History", b"history"), Button.inline("🗑️ Uninstall Bot", b"uninstall")],
        [Button.inline("ℹ️ Help", b"help")]
    ]
    return keyboard

# Initialize Telegram client
client = TelegramClient('bot_session', CONFIG['api_id'], CONFIG['api_hash'])

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handle /start command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ **Access Denied**\n\nYou are not authorized to use this bot.")
        logger.warning(f"Unauthorized access attempt by {username} ({user_id})")
        return
    
    log_command(user_id, username, "/start")
    
    welcome_message = f"""
🤖 **Welcome to {CONFIG['device_name']} Bot!**

✅ **Bot Status**: Online and Ready
🔧 **Device**: {CONFIG['device_name']}
👤 **User**: {username}
🆔 **Your ID**: `{user_id}`

**Available Commands:**
• Use buttons below for quick access
• Type `/help` for detailed command list
• Admin commands available for authorized users

**Quick Actions:**
"""
    
    keyboard = get_admin_keyboard() if is_admin(user_id) else get_main_keyboard()
    await event.respond(welcome_message, buttons=keyboard)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/help")
    
    help_text = f"""
🤖 **{CONFIG['device_name']} Bot Help**

**📊 System Commands:**
• `/system` - System information
• `/reboot` - Restart device
• `/clearram` - Clear RAM cache

**🌐 Network Commands:**
• `/network` - Network statistics
• `/speedtest` - Internet speed test
• `/ping [target]` - Ping test
• `/wifi` - WiFi information
• `/firewall` - Firewall status

**👥 User Commands:**
• `/userlist` - Connected devices
• `/backup` - System backup
• `/stats` - Bot statistics

**🔧 Maintenance:**
• `/update` - Update bot (Admin only)
• `/uninstall` - Remove bot (Admin only)
• `/history` - Command history (Admin only)

**💡 Tips:**
• Use buttons for quick access
• Commands are case-sensitive
• Some commands require admin privileges

**📞 Support:**
• Telegram: @ValltzID
• Website: revd.cloud
"""
    
    keyboard = get_admin_keyboard() if is_admin(user_id) else get_main_keyboard()
    await event.respond(help_text, buttons=keyboard)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    """Handle button callbacks."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    data = event.data.decode('utf-8')
    
    if not is_authorized(user_id):
        await event.answer("❌ Access denied.", alert=True)
        return
    
    # Admin-only commands
    admin_commands = ['update', 'uninstall', 'history']
    if data in admin_commands and not is_admin(user_id):
        await event.answer("❌ Admin access required.", alert=True)
        return
    
    log_command(user_id, username, f"button:{data}")
    
    try:
        await event.answer("⏳ Processing...")
        
        if data == "system":
            await handle_system_command(event)
        elif data == "reboot":
            await handle_reboot_command(event)
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
        elif data == "update":
            await handle_update_command(event)
        elif data == "uninstall":
            await handle_uninstall_command(event)
        elif data == "history":
            await handle_history_command(event)
        elif data == "help":
            await help_handler(event)
        else:
            await event.respond("❌ Unknown command.")
            
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        bot_stats['errors_count'] += 1
        await event.respond(f"❌ Error processing command: {str(e)}")

async def handle_system_command(event):
    """Handle system info command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/system.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_reboot_command(event):
    """Handle reboot command with confirmation."""
    user_id = event.sender_id
    
    # Create confirmation keyboard
    confirm_keyboard = [
        [Button.inline("✅ Yes, Reboot", b"confirm_reboot"), Button.inline("❌ Cancel", b"cancel_reboot")]
    ]
    
    await event.respond(
        "⚠️ **Reboot Confirmation**\n\n"
        "Are you sure you want to reboot the device?\n"
        "The device will be offline for 1-2 minutes.",
        buttons=confirm_keyboard
    )

@client.on(events.CallbackQuery(data=b"confirm_reboot"))
async def confirm_reboot_handler(event):
    """Handle reboot confirmation."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.answer("❌ Access denied.", alert=True)
        return
    
    log_command(user_id, username, "reboot_confirmed")
    
    await event.answer("🔄 Rebooting device...")
    await event.respond("🔄 **Rebooting Device**\n\nDevice is restarting... Please wait 1-2 minutes.")
    
    # Execute reboot
    await run_shell_command("sh /root/REVDBOT/plugins/reboot.sh")

@client.on(events.CallbackQuery(data=b"cancel_reboot"))
async def cancel_reboot_handler(event):
    """Handle reboot cancellation."""
    await event.answer("❌ Reboot cancelled.")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond("❌ Reboot cancelled.", buttons=keyboard)

async def handle_clearram_command(event):
    """Handle clear RAM command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/clear_ram.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_network_command(event):
    """Handle network stats command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/vnstat.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_speedtest_command(event):
    """Handle speedtest command."""
    await event.respond("🚀 **Running Speed Test**\n\nPlease wait, this may take 30-60 seconds...")
    result = await run_shell_command("sh /root/REVDBOT/plugins/speedtest.sh", timeout=120)
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_ping_command(event, target="google.com"):
    """Handle ping command."""
    result = await run_shell_command(f"sh /root/REVDBOT/plugins/ping.sh {target}")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_wifi_command(event):
    """Handle WiFi info command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/wifi.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_firewall_command(event):
    """Handle firewall status command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/firewall.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_userlist_command(event):
    """Handle user list command."""
    result = await run_shell_command("sh /root/REVDBOT/plugins/userlist.sh")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_backup_command(event):
    """Handle backup command."""
    await event.respond("💾 **Creating System Backup**\n\nPlease wait...")
    result = await run_shell_command("sh /root/REVDBOT/plugins/backup.sh", timeout=60)
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(f"```\n{result}\n```", buttons=keyboard)

async def handle_stats_command(event):
    """Handle bot statistics command."""
    uptime = datetime.now() - bot_stats['start_time']
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    stats_text = f"""
📈 **Bot Statistics**

**⏱️ Uptime:** {uptime_str}
**📊 Commands Executed:** {bot_stats['commands_executed']}
**❌ Errors:** {bot_stats['errors_count']}
**👥 Active Users:** {len(bot_stats['user_activity'])}

**📋 Last Command:**
"""
    
    if bot_stats['last_command']:
        last_cmd = bot_stats['last_command']
        stats_text += f"• {last_cmd['command']} by {last_cmd['username']}\n• Time: {last_cmd['timestamp']}"
    else:
        stats_text += "• No commands executed yet"
    
    stats_text += f"\n\n**🔧 Device:** {CONFIG['device_name']}"
    stats_text += f"\n**🤖 Bot Version:** Enhanced Edition v2.0"
    
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond(stats_text, buttons=keyboard)

async def handle_update_command(event):
    """Handle bot update command (admin only)."""
    if not is_admin(event.sender_id):
        await event.respond("❌ Admin access required.")
        return
    
    # Create confirmation keyboard
    confirm_keyboard = [
        [Button.inline("✅ Yes, Update", b"confirm_update"), Button.inline("❌ Cancel", b"cancel_update")]
    ]
    
    await event.respond(
        "⬆️ **Bot Update Confirmation**\n\n"
        "This will update the bot to the latest version from GitHub.\n"
        "The bot will restart after update.\n\n"
        "Continue?",
        buttons=confirm_keyboard
    )

@client.on(events.CallbackQuery(data=b"confirm_update"))
async def confirm_update_handler(event):
    """Handle update confirmation."""
    if not is_admin(event.sender_id):
        await event.answer("❌ Admin access required.", alert=True)
        return
    
    username = event.sender.username or event.sender.first_name or "Unknown"
    log_command(event.sender_id, username, "update_confirmed")
    
    await event.answer("⬆️ Starting update...")
    await event.respond("⬆️ **Updating Bot**\n\nDownloading latest version... Please wait.")
    
    # Execute update
    result = await run_shell_command("sh /root/REVDBOT/plugins/update.sh", timeout=120)
    await event.respond(f"```\n{result}\n```")

@client.on(events.CallbackQuery(data=b"cancel_update"))
async def cancel_update_handler(event):
    """Handle update cancellation."""
    await event.answer("❌ Update cancelled.")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond("❌ Update cancelled.", buttons=keyboard)

async def handle_uninstall_command(event):
    """Handle bot uninstall command (admin only)."""
    if not is_admin(event.sender_id):
        await event.respond("❌ Admin access required.")
        return
    
    # Create confirmation keyboard
    confirm_keyboard = [
        [Button.inline("🗑️ Delete All", b"uninstall_all")],
        [Button.inline("💾 Keep Config", b"uninstall_keep")],
        [Button.inline("❌ Cancel", b"cancel_uninstall")]
    ]
    
    await event.respond(
        "🗑️ **Bot Uninstall Confirmation**\n\n"
        "⚠️ **WARNING**: This will remove the bot from your system!\n\n"
        "**Options:**\n"
        "• **Delete All**: Remove everything\n"
        "• **Keep Config**: Save configuration for future reinstall\n"
        "• **Cancel**: Abort uninstall\n\n"
        "Choose wisely:",
        buttons=confirm_keyboard
    )

@client.on(events.CallbackQuery(data=b"uninstall_all"))
async def uninstall_all_handler(event):
    """Handle complete uninstall."""
    if not is_admin(event.sender_id):
        await event.answer("❌ Admin access required.", alert=True)
        return
    
    username = event.sender.username or event.sender.first_name or "Unknown"
    log_command(event.sender_id, username, "uninstall_all")
    
    await event.answer("🗑️ Uninstalling bot...")
    await event.respond("🗑️ **Uninstalling Bot**\n\nRemoving all files... Goodbye! 👋")
    
    # Execute uninstall
    await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh n")

@client.on(events.CallbackQuery(data=b"uninstall_keep"))
async def uninstall_keep_handler(event):
    """Handle uninstall with config backup."""
    if not is_admin(event.sender_id):
        await event.answer("❌ Admin access required.", alert=True)
        return
    
    username = event.sender.username or event.sender.first_name or "Unknown"
    log_command(event.sender_id, username, "uninstall_keep_config")
    
    await event.answer("💾 Uninstalling with backup...")
    await event.respond("💾 **Uninstalling Bot**\n\nSaving configuration backup... You can reinstall later!")
    
    # Execute uninstall with config backup
    await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh y")

@client.on(events.CallbackQuery(data=b"cancel_uninstall"))
async def cancel_uninstall_handler(event):
    """Handle uninstall cancellation."""
    await event.answer("❌ Uninstall cancelled.")
    keyboard = get_admin_keyboard() if is_admin(event.sender_id) else get_main_keyboard()
    await event.respond("❌ Uninstall cancelled. Bot remains active.", buttons=keyboard)

async def handle_history_command(event):
    """Handle command history (admin only)."""
    if not is_admin(event.sender_id):
        await event.respond("❌ Admin access required.")
        return
    
    if not bot_stats['command_history']:
        await event.respond("📜 **Command History**\n\nNo commands executed yet.")
        return
    
    history_text = "📜 **Command History** (Last 10)\n\n"
    
    # Show last 10 commands
    recent_commands = bot_stats['command_history'][-10:]
    for i, cmd in enumerate(reversed(recent_commands), 1):
        history_text += f"**{i}.** `{cmd['command']}`\n"
        history_text += f"   👤 {cmd['username']} • 🕒 {cmd['timestamp']}\n\n"
    
    history_text += f"**Total Commands:** {bot_stats['commands_executed']}"
    
    keyboard = get_admin_keyboard()
    await event.respond(history_text, buttons=keyboard)

# Text command handlers
@client.on(events.NewMessage(pattern='/system'))
async def system_command(event):
    """Handle /system command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/system")
    await handle_system_command(event)

@client.on(events.NewMessage(pattern=r'/ping(?:\s+(.+))?'))
async def ping_command(event):
    """Handle /ping command with optional target."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    target = event.pattern_match.group(1) or "google.com"
    log_command(user_id, username, f"/ping {target}")
    await handle_ping_command(event, target)

@client.on(events.NewMessage(pattern='/network'))
async def network_command(event):
    """Handle /network command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/network")
    await handle_network_command(event)

@client.on(events.NewMessage(pattern='/speedtest'))
async def speedtest_command(event):
    """Handle /speedtest command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/speedtest")
    await handle_speedtest_command(event)

@client.on(events.NewMessage(pattern='/clearram'))
async def clearram_command(event):
    """Handle /clearram command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/clearram")
    await handle_clearram_command(event)

@client.on(events.NewMessage(pattern='/wifi'))
async def wifi_command(event):
    """Handle /wifi command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/wifi")
    await handle_wifi_command(event)

@client.on(events.NewMessage(pattern='/firewall'))
async def firewall_command(event):
    """Handle /firewall command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/firewall")
    await handle_firewall_command(event)

@client.on(events.NewMessage(pattern='/userlist'))
async def userlist_command(event):
    """Handle /userlist command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/userlist")
    await handle_userlist_command(event)

@client.on(events.NewMessage(pattern='/backup'))
async def backup_command(event):
    """Handle /backup command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/backup")
    await handle_backup_command(event)

@client.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Handle /stats command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/stats")
    await handle_stats_command(event)

# Admin-only commands
@client.on(events.NewMessage(pattern='/update'))
async def update_command(event):
    """Handle /update command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ Admin access required.")
        return
    
    log_command(user_id, username, "/update")
    await handle_update_command(event)

@client.on(events.NewMessage(pattern='/uninstall'))
async def uninstall_command(event):
    """Handle /uninstall command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ Admin access required.")
        return
    
    log_command(user_id, username, "/uninstall")
    await handle_uninstall_command(event)

@client.on(events.NewMessage(pattern='/history'))
async def history_command(event):
    """Handle /history command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ Admin access required.")
        return
    
    log_command(user_id, username, "/history")
    await handle_history_command(event)

# Handle unauthorized messages
@client.on(events.NewMessage)
async def unauthorized_handler(event):
    """Handle messages from unauthorized users."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized message from {username} ({user_id}): {event.text}")
        await event.respond(
            "❌ **Access Denied**\n\n"
            "You are not authorized to use this bot.\n"
            "Contact the administrator for access."
        )

async def send_startup_notification():
    """Send startup notification to admin."""
    if not CONFIG['notification_enabled']:
        return
    
    try:
        startup_message = f"""
🚀 **Bot Started Successfully**

✅ **Status**: Online and Ready
🔧 **Device**: {CONFIG['device_name']}
⏰ **Started**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **Version**: Enhanced Edition v2.0

**Configuration:**
• Admin ID: {CONFIG['admin_id']}
• Allowed Users: {len(CONFIG['allowed_users'])}
• Auto Backup: {'✅' if CONFIG['auto_backup'] else '❌'}

Bot is ready to receive commands!
"""
        
        await client.send_message(CONFIG['admin_id'], startup_message)
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