#!/bin/sh

# Update script for OpenWRT Telegram Bot 
# This script should be placed in the plugins directory

# Define the GitHub repository and directories
GITHUB_REPO="https://github.com/revaldieka/telebotaku.git"
ROOT_DIR="/root/REVDBOT"
TEMP_DIR="/tmp/bot_update_temp"
PLUGINS_DIR="$ROOT_DIR/plugins"

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
    mkdir -p "$PLUGINS_DIR"
    for plugin in "$TEMP_DIR/plugins"/*; do
        if [ -f "$plugin" ]; then
            plugin_name=$(basename "$plugin")
            cp "$plugin" "$PLUGINS_DIR/$plugin_name"
            chmod +x "$PLUGINS_DIR/$plugin_name"
            echo "  ✓ Updated plugin: $plugin_name"
        fi
    done
else
    echo "  ⚠️ No plugins directory found in update."
fi

# Install or update the post-update notification script
echo "📣 Setting up post-update notification..."
cat > "$PLUGINS_DIR/post_update.sh" << 'EOF'
#!/bin/sh

# Post-update notification script for OpenWRT Telegram Bot
# This script should be placed in the plugins directory

# Configuration file path
CONFIG_PATH="/root/REVDBOT/config.ini"

# Function to read values from config file
read_config() {
    local section="$1"
    local key="$2"
    local file="$3"
    
    # Use grep and sed to extract the value from the config file
    grep -A 10 "^\[$section\]" "$file" | grep "^$key\s*=" | sed 's/^[^=]*=\s*//'
}

# Read the configuration
if [ -f "$CONFIG_PATH" ]; then
    API_ID=$(read_config "Telegram" "api_id" "$CONFIG_PATH")
    API_HASH=$(read_config "Telegram" "api_hash" "$CONFIG_PATH")
    BOT_TOKEN=$(read_config "Telegram" "bot_token" "$CONFIG_PATH")
    ADMIN_ID=$(read_config "Telegram" "admin_id" "$CONFIG_PATH")
    
    if [ -z "$API_ID" ] || [ -z "$API_HASH" ] || [ -z "$BOT_TOKEN" ] || [ -z "$ADMIN_ID" ]; then
        echo "❌ Error: Missing configuration values"
        exit 1
    fi
else
    echo "❌ Error: Config file not found at $CONFIG_PATH"
    exit 1
fi

# Wait for bot to fully start (adjust if needed)
sleep 15

# Get current date and time
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Send success notification using curl and Telegram API
MESSAGE="✅ *Bot Update Completed* ($TIMESTAMP)

The bot has been successfully updated and is now running.
You can continue using all bot functions as normal.

_If you notice any issues with the new version, you can restore the backup using the instructions from the update log._"

# URL encode the message
MESSAGE=$(echo "$MESSAGE" | sed 's/ /%20/g; s/\n/%0A/g; s/\*/%2A/g; s/_/%5F/g')

# Send message using Telegram API
curl -s "https://api.telegram.org/bot$BOT_TOKEN/sendMessage?chat_id=$ADMIN_ID&text=$MESSAGE&parse_mode=Markdown" > /dev/null

echo "Notification sent to admin ($ADMIN_ID)"
EOF

# Make the post-update script executable
chmod +x "$PLUGINS_DIR/post_update.sh"

# Clean up
rm -rf "$TEMP_DIR"
echo "🧹 Cleaned up temporary files."

# Create a trigger script to run post_update.sh after reboot
echo "📝 Creating update notification trigger..."
cat > "/tmp/run_post_update.sh" << 'EOF'
#!/bin/sh
# Wait a bit for services to start
sleep 5
# Run the post-update notification script
/root/REVDBOT/plugins/post_update.sh &
EOF

chmod +x "/tmp/run_post_update.sh"

# Restart bot service
echo "🔄 Restarting bot service..."
if /etc/init.d/revd restart; then
    echo "✅ Bot service restarted successfully."
    # Run the post-update trigger in the background
    /bin/sh /tmp/run_post_update.sh &
    echo "📣 Post-update notification scheduled."
else
    echo "⚠️ Failed to restart service. Please restart manually with: /etc/init.d/revd restart"
fi

echo "
✅ Update completed successfully!
Bot has been updated to the latest version.
If you encounter any issues, you can restore the backup:
  cp $ROOT_DIR/bot_openwrt.py.bak $ROOT_DIR/bot_openwrt.py"
