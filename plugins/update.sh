#!/bin/sh

# Update script for OpenWRT Telegram Bot 
# This script should be placed in the plugins directory

# Define the GitHub repository and directories
GITHUB_REPO="https://github.com/revaldieka/telebotaku.git"
ROOT_DIR="/root/REVDBOT"
TEMP_DIR="/tmp/bot_update_temp"

# Create temporary directory for update
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi
mkdir -p "$TEMP_DIR"

echo "🔄 Starting bot update process..."

# Clone the repository to temporary directory
echo "📥 Downloading updates from GitHub..."
if git clone "$GITHUB_REPO" "$TEMP_DIR"; then
    echo "✅ Repository cloned successfully."
else
    echo "❌ Failed to clone repository. Check your internet connection."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Check if update files exist
if [ ! -f "$TEMP_DIR/bot_openwrt.py" ]; then
    echo "❌ Update files not found in repository."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Backup current files
echo "💾 Creating backup of current files..."
cp "$ROOT_DIR/bot_openwrt.py" "$ROOT_DIR/bot_openwrt.py.bak" 2>/dev/null

# Update main bot script
echo "📝 Updating main bot script..."
cp "$TEMP_DIR/bot_openwrt.py" "$ROOT_DIR/bot_openwrt.py"
chmod +x "$ROOT_DIR/bot_openwrt.py"

# Update plugins
echo "🔌 Updating plugins..."
if [ -d "$TEMP_DIR/plugins" ]; then
    mkdir -p "$ROOT_DIR/plugins"
    for plugin in "$TEMP_DIR/plugins"/*; do
        if [ -f "$plugin" ]; then
            plugin_name=$(basename "$plugin")
            cp "$plugin" "$ROOT_DIR/plugins/$plugin_name"
            chmod +x "$ROOT_DIR/plugins/$plugin_name"
            echo "  ✓ Updated plugin: $plugin_name"
        fi
    done
else
    echo "  ⚠️ No plugins directory found in update."
fi

# Add startup notification script
echo "📣 Adding startup notification script..."
cat > "$ROOT_DIR/plugins/bot_startup_notification.py" << 'EOF'
import os
import re
import logging
import configparser
import time
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/tmp/bot_notification.log'
)
logger = logging.getLogger("startup_notifier")

def load_config():
    """Load configuration from config.ini."""
    config = {
        'api_id': '',
        'api_hash': '',
        'bot_token': '',
        'admin_id': 0,
    }

    # Try to load from config file
    script_dir = Path(__file__).parent.parent
    config_file = script_dir / 'config.ini'
    
    if not config_file.exists():
        logger.error("Config file not found: %s", config_file)
        return None
    
    try:
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        if 'Telegram' in parser:
            config['api_id'] = parser['Telegram'].get('api_id', '')
            config['api_hash'] = parser['Telegram'].get('api_hash', '')
            config['bot_token'] = parser['Telegram'].get('bot_token', '')
            config['admin_id'] = int(parser['Telegram'].get('admin_id', 0))
        
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def check_update_flag():
    """Check if update flag file exists."""
    flag_file = Path("/tmp/bot_updated")
    return flag_file.exists()

def send_notification():
    """Send notification to admin."""
    try:
        # Load config
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return False
            
        # Get bot token and admin ID
        bot_token = config['bot_token']
        admin_id = config['admin_id']
        
        if not bot_token or admin_id == 0:
            logger.error("Missing bot token or admin ID")
            return False
            
        # Current time
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Check for custom update message
        custom_message_file = Path("/root/REVDBOT/update_message.txt")
        if custom_message_file.exists():
            try:
                with open(custom_message_file, "r") as f:
                    custom_message = f.read().strip()
                logger.info("Using custom update message")
                
                # Message to send with custom content
                message = f"✅ *Bot Update Completed Successfully* ({current_time})\n\n{custom_message}"
            except Exception as e:
                logger.error(f"Error reading custom message: {str(e)}")
                # Fall back to default message
                default_message = True
        else:
            # Use default message
            default_message = True
            
        # Default message if no custom message is available
        if 'default_message' in locals() and default_message:
            # Update list
            update_list = """
🔄 *Daftar Pembaruan:*
• Peningkatan stabilitas sistem
• Perbaikan bug dan error
• Pengoptimalan performa bot
• Penambahan fitur baru
• Peningkatan keamanan sistem
"""

            # Donation information
            donation_info = """
💰 *Jika teman2 ingin berdonasi bisa ke:*
DANA - OVO - GOPAY
Nomor 088214672165
an. Revaldi Eka Maulana.
"""
            
            # Message to send
            message = f"✅ *Bot Update Completed Successfully* ({current_time})\n\n" \
                    f"The bot has been updated and is now running normally.\n" \
                    f"You can continue using all bot functions.\n" \
                    f"{update_list}\n{donation_info}"
                  
        # Send message
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": admin_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logger.info(f"Update notification sent to admin {admin_id}")
            return True
        else:
            logger.error(f"Failed to send notification: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return False

def clear_update_flag():
    """Clear the update flag file."""
    flag_file = Path("/tmp/bot_updated")
    if flag_file.exists():
        flag_file.unlink()
        logger.info("Update flag cleared")

if __name__ == "__main__":
    # Wait a bit for network and services to start
    time.sleep(10)
    
    # Check if this is a post-update startup
    if check_update_flag():
        logger.info("Bot was updated, sending notification")
        if send_notification():
            clear_update_flag()
    else:
        logger.info("No update flag found, skipping notification")
EOF

# Modify bot startup script to run notification
echo "📝 Creating bot startup wrapper..."
cat > "$ROOT_DIR/start_bot.sh" << 'EOF'
#!/bin/sh

# Startup wrapper for bot that includes notification functionality
cd "$(dirname "$0")"

# Run the notification script to check for update flag
python3 plugins/bot_startup_notification.py &

# Start the main bot
python3 bot_openwrt.py
EOF

chmod +x "$ROOT_DIR/start_bot.sh"
chmod +x "$ROOT_DIR/plugins/bot_startup_notification.py"

# Create or modify init.d script to use the wrapper
echo "📝 Updating init.d script..."
cat > "/etc/init.d/revd" << 'EOF'
#!/bin/sh /etc/rc.common

START=99
STOP=15
USE_PROCD=1

start_service() {
    procd_open_instance
    procd_set_param command /root/REVDBOT/start_bot.sh
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_set_param respawn ${respawn_threshold:-3600} ${respawn_timeout:-5} ${respawn_retry:-5}
    procd_close_instance
}
EOF

chmod +x "/etc/init.d/revd"

# Create update flag
echo "🚩 Setting update flag..."
touch "/tmp/bot_updated"

# Create default custom message file if it doesn't exist
if [ ! -f "$ROOT_DIR/update_message.txt" ]; then
    echo "📝 Creating custom message template file..."
    cat > "$ROOT_DIR/update_message.txt" << 'EOF'
Bot telah diperbarui dan sedang berjalan dengan normal.
Anda dapat melanjutkan penggunaan semua fungsi bot.

🔄 *Daftar Pembaruan:*
• Peningkatan stabilitas sistem
• Perbaikan bug dan error
• Pengoptimalan performa bot
• Penambahan fitur baru
• Peningkatan keamanan sistem

💰 *Jika teman2 ingin berdonasi bisa ke:*
DANA - OVO - GOPAY
Nomor 088214672165
an. Revaldi Eka Maulana.

Terima kasih telah menggunakan bot ini! 🙏
EOF
    echo "✅ Custom message template created at $ROOT_DIR/update_message.txt"
fi

# Clean up
rm -rf "$TEMP_DIR"
echo "🧹 Cleaned up temporary files."

# Install required package for notification script
echo "📦 Checking for required packages..."
if ! opkg list-installed | grep -q "python3-requests"; then
    echo "📦 Installing python3-requests package..."
    opkg update && opkg install python3-requests
else
    echo "✓ python3-requests already installed."
fi

# Restart bot service
echo "🔄 Restarting bot service..."
if /etc/init.d/revd restart; then
    echo "✅ Bot service restarted successfully."
else
    echo "⚠️ Failed to restart service. Please restart manually with: /etc/init.d/revd restart"
fi

# Display donation information in terminal too
echo "
💰 Jika teman2 ingin berdonasi bisa ke:
DANA - OVO - GOPAY
Nomor 088214672165
an. Revaldi Eka Maulana.
"

echo "
✅ Update completed successfully!
Bot has been updated to the latest version.
A notification will be sent when the bot comes back online.

📝 Custom Update Message:
You can customize the update notification by editing:
  $ROOT_DIR/update_message.txt

If you encounter any issues, you can restore the backup:
  cp $ROOT_DIR/bot_openwrt.py.bak $ROOT_DIR/bot_openwrt.py"
