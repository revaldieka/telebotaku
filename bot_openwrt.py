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

def get_main_menu():
    """Generate main menu with device info."""
    device_info = get_device_info()
    
    menu_text = f"""
🤖 **{CONFIG['device_name']} Management Bot**

📡 **Device Information:**
• **Hostname:** {device_info['hostname']}
• **Version:** {device_info['version']}
• **Uptime:** {device_info['uptime']}

🔧 **Available Commands:**

**📊 System Management:**
• `/system` - System information & status
• `/reboot` - Restart device (with confirmation)
• `/clearram` - Clear RAM cache
• `/backup` - Create system backup

**🌐 Network Monitoring:**
• `/network` - Network statistics (vnstat)
• `/speedtest` - Internet speed test
• `/ping [target]` - Ping test (default: google.com)
• `/wifi` - WiFi information & clients
• `/firewall` - Firewall status & rules
• `/userlist` - Connected devices list

**📈 Bot Management:**
• `/stats` - Bot statistics & performance
• `/menu` - Show this menu
• `/help` - Detailed help information

**🔐 Admin Commands:**
• `/update` - Update bot from GitHub
• `/uninstall` - Remove bot from system
• `/history` - Command execution history

**💡 Tips:**
• Commands are case-sensitive
• Some commands require admin privileges
• Use `/help` for detailed command descriptions

**🌐 REVD.CLOUD Services:**
• **Website:** https://revd.cloud
• **Telegram:** @ValltzID
• **Instagram:** @revd.cloud
• **Support:** Professional OpenWRT solutions

**🚀 Bot Version:** Enhanced Edition v2.1
**⚡ Powered by:** REVD.CLOUD Technology
"""
    return menu_text

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
    
    device_info = get_device_info()
    
    welcome_message = f"""
🤖 **Welcome to {CONFIG['device_name']} Bot!**

✅ **Bot Status**: Online and Ready
🔧 **Device**: {device_info['hostname']}
📊 **Version**: {device_info['version']}
⏱️ **Uptime**: {device_info['uptime']}
👤 **User**: {username}
🆔 **Your ID**: `{user_id}`

**🌐 REVD.CLOUD Services:**
• Professional OpenWRT management solutions
• Custom bot development & deployment
• Network infrastructure consulting
• 24/7 technical support

**Quick Start:**
• Type `/menu` to see all available commands
• Type `/help` for detailed information
• Type `/system` for device status

**🚀 Ready to manage your OpenWRT device!**

**Contact & Support:**
• Website: https://revd.cloud
• Telegram: @ValltzID
• Instagram: @revd.cloud
"""
    
    await event.respond(welcome_message)

@client.on(events.NewMessage(pattern='/menu'))
async def menu_handler(event):
    """Handle /menu command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/menu")
    
    menu_text = get_main_menu()
    await event.respond(menu_text)

@client.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/help")
    
    device_info = get_device_info()
    
    help_text = f"""
🤖 **{CONFIG['device_name']} Bot - Detailed Help**

📡 **Device:** {device_info['hostname']} | **Version:** {device_info['version']}

**📊 System Commands:**
• `/system` - Complete system information (CPU, RAM, temperature, network)
• `/reboot` - Restart device with safety confirmation
• `/clearram` - Clear system RAM cache for better performance
• `/backup` - Create compressed system backup

**🌐 Network Commands:**
• `/network` - Network usage statistics via vnstat
• `/speedtest` - Internet speed test (download/upload/ping)
• `/ping [target]` - Network connectivity test (default: google.com)
• `/wifi` - WiFi networks, clients, and signal information
• `/firewall` - Firewall status, rules, and port forwards
• `/userlist` - List of connected devices with details

**📈 Bot Commands:**
• `/stats` - Bot performance and usage statistics
• `/menu` - Main menu with all commands
• `/help` - This detailed help information

**🔐 Admin-Only Commands:**
• `/update` - Update bot to latest version from GitHub
• `/uninstall` - Safely remove bot with backup options
• `/history` - View command execution history

**💡 Usage Tips:**
• All commands are case-sensitive
• Some operations may take 30-60 seconds
• Admin commands require elevated privileges
• Bot logs all activities for security

**🛡️ Security Features:**
• Multi-user authorization system
• Command logging and audit trail
• Session management and timeout protection
• Unauthorized access monitoring

**🌐 REVD.CLOUD Professional Services:**

**🔧 What We Offer:**
• Custom OpenWRT bot development
• Network infrastructure consulting
• Remote device management solutions
• 24/7 technical support and monitoring

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

**📋 Our Portfolio:**
• Telegram bot automation systems
• Network monitoring solutions
• Custom firmware development
• IoT device management platforms

**🎯 Get Professional Support:**
Contact us for custom bot features, enterprise deployments, or technical consulting services.

**⚡ Powered by REVD.CLOUD Technology**
"""
    
    await event.respond(help_text)

@client.on(events.NewMessage(pattern='/system'))
async def system_command(event):
    """Handle /system command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/system")
    
    # Send processing message
    processing_msg = await event.respond("⏳ **Getting system information...**\n\nPlease wait while I collect system data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/system.sh")
    
    # Edit the processing message with results
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/reboot'))
async def reboot_command(event):
    """Handle /reboot command with confirmation."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/reboot")
    
    device_info = get_device_info()
    
    confirm_msg = f"""
⚠️ **Reboot Confirmation Required**

**Device:** {device_info['hostname']}
**Current Uptime:** {device_info['uptime']}

**Warning:** This will restart your OpenWRT device!
• Device will be offline for 1-2 minutes
• All active connections will be dropped
• Services will restart automatically

**To confirm reboot, type:** `/reboot confirm`
**To cancel, ignore this message or type any other command.**

**Note:** Only proceed if you're sure about rebooting the device.
"""
    
    await event.respond(confirm_msg)

@client.on(events.NewMessage(pattern='/reboot confirm'))
async def reboot_confirm_command(event):
    """Handle reboot confirmation."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/reboot confirm")
    
    device_info = get_device_info()
    
    reboot_msg = await event.respond(f"🔄 **Rebooting {device_info['hostname']}**\n\nDevice is restarting... Please wait 1-2 minutes before reconnecting.")
    
    # Execute reboot
    await run_shell_command("sh /root/REVDBOT/plugins/reboot.sh")

@client.on(events.NewMessage(pattern='/clearram'))
async def clearram_command(event):
    """Handle /clearram command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/clearram")
    
    processing_msg = await event.respond("🧹 **Clearing RAM cache...**\n\nOptimizing memory usage...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/clear_ram.sh")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/network'))
async def network_command(event):
    """Handle /network command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/network")
    
    processing_msg = await event.respond("📊 **Collecting network statistics...**\n\nAnalyzing network usage data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/vnstat.sh")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/speedtest'))
async def speedtest_command(event):
    """Handle /speedtest command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/speedtest")
    
    processing_msg = await event.respond("🚀 **Running Internet Speed Test**\n\nTesting download/upload speeds...\nThis may take 30-60 seconds.")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/speedtest.sh", timeout=120)
    await processing_msg.edit(f"```\n{result}\n```")

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
    
    processing_msg = await event.respond(f"📡 **Testing connection to {target}**\n\nSending ping packets...")
    
    result = await run_shell_command(f"sh /root/REVDBOT/plugins/ping.sh {target}")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/wifi'))
async def wifi_command(event):
    """Handle /wifi command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/wifi")
    
    processing_msg = await event.respond("📶 **Scanning WiFi information...**\n\nGathering wireless network data...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/wifi.sh")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/firewall'))
async def firewall_command(event):
    """Handle /firewall command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/firewall")
    
    processing_msg = await event.respond("🔥 **Checking firewall status...**\n\nAnalyzing security rules...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/firewall.sh")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/userlist'))
async def userlist_command(event):
    """Handle /userlist command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/userlist")
    
    processing_msg = await event.respond("👥 **Scanning connected devices...**\n\nListing active network clients...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/userlist.sh")
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/backup'))
async def backup_command(event):
    """Handle /backup command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/backup")
    
    processing_msg = await event.respond("💾 **Creating System Backup**\n\nBacking up configuration and settings...")
    
    result = await run_shell_command("sh /root/REVDBOT/plugins/backup.sh", timeout=60)
    await processing_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/stats'))
async def stats_command(event):
    """Handle /stats command."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_authorized(user_id):
        await event.respond("❌ Access denied.")
        return
    
    log_command(user_id, username, "/stats")
    
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
• **Active Users:** {len(bot_stats['user_activity'])}

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
**👥 User Activity:**
"""
    
    if bot_stats['user_activity']:
        for user_id, activity in list(bot_stats['user_activity'].items())[:5]:
            stats_text += f"• **{activity['username']}:** {activity['count']} commands\n"
    else:
        stats_text += "• No user activity recorded\n"
    
    stats_text += f"""
**🌐 REVD.CLOUD Services:**
• Professional OpenWRT solutions
• Custom bot development
• Network consulting services
• 24/7 technical support

**📞 Contact:** @ValltzID | https://revd.cloud
"""
    
    await event.respond(stats_text)

# Admin-only commands
@client.on(events.NewMessage(pattern='/update'))
async def update_command(event):
    """Handle /update command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ **Admin Access Required**\n\nThis command is restricted to administrators only.")
        return
    
    log_command(user_id, username, "/update")
    
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

**To confirm update, type:** `/update confirm`
**To cancel, ignore this message.**

**Note:** Your configuration will be preserved.
"""
    
    await event.respond(confirm_msg)

@client.on(events.NewMessage(pattern='/update confirm'))
async def update_confirm_command(event):
    """Handle update confirmation."""
    if not is_admin(event.sender_id):
        await event.respond("❌ Admin access required.")
        return
    
    username = event.sender.username or event.sender.first_name or "Unknown"
    log_command(event.sender_id, username, "/update confirm")
    
    update_msg = await event.respond("⬆️ **Starting Bot Update**\n\nDownloading latest version from GitHub...\nPlease wait...")
    
    # Execute update
    result = await run_shell_command("sh /root/REVDBOT/plugins/update.sh", timeout=120)
    await update_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/uninstall'))
async def uninstall_command(event):
    """Handle /uninstall command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ **Admin Access Required**\n\nThis command is restricted to administrators only.")
        return
    
    log_command(user_id, username, "/uninstall")
    
    device_info = get_device_info()
    
    confirm_msg = f"""
🗑️ **Bot Uninstall Confirmation**

**Device:** {device_info['hostname']}
**Bot Version:** Enhanced Edition v2.1

⚠️ **WARNING:** This will completely remove the bot from your system!

**Uninstall Options:**
• **Complete Removal:** `/uninstall confirm delete` - Remove everything
• **Keep Config:** `/uninstall confirm keep` - Save configuration for future reinstall
• **Cancel:** Ignore this message

**What will be removed:**
• Bot service and startup scripts
• All bot files and plugins
• Log files and session data
• Service configuration

**Note:** Configuration backup will be saved to `/etc/revd_backup/` if you choose "keep" option.
"""
    
    await event.respond(confirm_msg)

@client.on(events.NewMessage(pattern='/uninstall confirm (delete|keep)'))
async def uninstall_confirm_command(event):
    """Handle uninstall confirmation."""
    if not is_admin(event.sender_id):
        await event.respond("❌ Admin access required.")
        return
    
    username = event.sender.username or event.sender.first_name or "Unknown"
    option = event.pattern_match.group(1)
    log_command(event.sender_id, username, f"/uninstall confirm {option}")
    
    if option == "keep":
        uninstall_msg = await event.respond("💾 **Uninstalling with Configuration Backup**\n\nSaving configuration and removing bot...\nYou can reinstall later with saved settings!")
        result = await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh y")
    else:
        uninstall_msg = await event.respond("🗑️ **Complete Bot Removal**\n\nRemoving all bot files and configuration...\nGoodbye! 👋")
        result = await run_shell_command("sh /root/REVDBOT/plugins/uninstall.sh n")
    
    await uninstall_msg.edit(f"```\n{result}\n```")

@client.on(events.NewMessage(pattern='/history'))
async def history_command(event):
    """Handle /history command (admin only)."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    if not is_admin(user_id):
        await event.respond("❌ **Admin Access Required**\n\nThis command is restricted to administrators only.")
        return
    
    log_command(user_id, username, "/history")
    
    if not bot_stats['command_history']:
        await event.respond("📜 **Command History**\n\nNo commands have been executed yet.")
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
    
    await event.respond(history_text)

# Handle unauthorized messages
@client.on(events.NewMessage)
async def unauthorized_handler(event):
    """Handle messages from unauthorized users."""
    user_id = event.sender_id
    username = event.sender.username or event.sender.first_name or "Unknown"
    
    # Skip if user is authorized
    if is_authorized(user_id):
        return
    
    # Skip if message starts with known commands (already handled)
    message_text = event.text.lower()
    known_commands = ['/start', '/help', '/menu', '/system', '/reboot', '/clearram', 
                     '/network', '/speedtest', '/ping', '/wifi', '/firewall', 
                     '/userlist', '/backup', '/stats', '/update', '/uninstall', '/history']
    
    if any(message_text.startswith(cmd) for cmd in known_commands):
        return
    
    logger.warning(f"Unauthorized message from {username} ({user_id}): {event.text}")
    await event.respond(
        f"❌ **Access Denied**\n\n"
        f"You are not authorized to use this bot.\n"
        f"Contact the administrator for access.\n\n"
        f"**🌐 REVD.CLOUD Services:**\n"
        f"For professional OpenWRT solutions and custom bot development:\n"
        f"• Website: https://revd.cloud\n"
        f"• Telegram: @ValltzID\n"
        f"• Instagram: @revd.cloud"
    )

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
• **Allowed Users:** {len(CONFIG['allowed_users'])}
• **Auto Backup:** {'✅' if CONFIG['auto_backup'] else '❌'}
• **Notifications:** {'✅' if CONFIG['notification_enabled'] else '❌'}

**🌐 REVD.CLOUD Services:**
Professional OpenWRT management solutions now available!
• Custom bot development
• Network infrastructure consulting  
• 24/7 technical support
• Enterprise deployment services

**📞 Contact:** @ValltzID | https://revd.cloud

**🚀 Bot is ready to receive commands!**
Type `/menu` to see all available commands.
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