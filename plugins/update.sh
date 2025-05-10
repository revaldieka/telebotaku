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

# Clean up
rm -rf "$TEMP_DIR"
echo "🧹 Cleaned up temporary files."

# Restart bot service
echo "🔄 Restarting bot service..."
if /etc/init.d/revd restart; then
    echo "✅ Bot service restarted successfully."
else
    echo "⚠️ Failed to restart service. Please restart manually with: /etc/init.d/revd restart"
fi

echo "
✅ Update completed successfully!
Bot has been updated to the latest version.
If you encounter any issues, you can restore the backup:
  cp $ROOT_DIR/bot_openwrt.py.bak $ROOT_DIR/bot_openwrt.py"
