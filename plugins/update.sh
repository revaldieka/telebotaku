#!/bin/sh

# OpenWRT Telegram Bot Update Script
# Created based on REVD.CLOUD installer

echo "
╔═══════════════════════════════════╗
║  OpenWRT Telegram Bot Updater     ║
║           REVD.CLOUD              ║
╚═══════════════════════════════════╝
"

# Define paths
ROOT_DIR="/root/REVDBOT"
PLUGINS_DIR="$ROOT_DIR/plugins"
GITHUB_REPO="https://github.com/revaldieka/telebotaku.git"
TEMP_DIR="/tmp/bot_update"
LOG_FILE="/var/log/revd_update.log"

# Log function
log_message() {
    echo "$(date): $1" >> "$LOG_FILE"
    echo "$1"
}

log_message "Starting bot update process..."

# Create temp directory for update
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi
mkdir -p "$TEMP_DIR"

# Clone repository to temp directory
log_message "Cloning repository from GitHub..."
if git clone "$GITHUB_REPO" "$TEMP_DIR"; then
    log_message "Repository cloned successfully."
else
    log_message "Failed to clone repository. Check your internet connection."
    exit 1
fi

# Backup current bot script
log_message "Backing up current bot script..."
cp "$ROOT_DIR/bot_openwrt.py" "$ROOT_DIR/bot_openwrt.py.bak" 2>/dev/null

# Update bot_openwrt.py
if [ -f "$TEMP_DIR/bot_openwrt.py" ]; then
    log_message "Updating main bot script..."
    cp "$TEMP_DIR/bot_openwrt.py" "$ROOT_DIR/bot_openwrt.py"
    chmod +x "$ROOT_DIR/bot_openwrt.py"
else
    log_message "Warning: bot_openwrt.py not found in repository."
fi

# Update plugins
if [ -d "$TEMP_DIR/plugins" ]; then
    log_message "Updating plugin scripts..."
    
    # Create plugins directory if it doesn't exist
    if [ ! -d "$PLUGINS_DIR" ]; then
        mkdir -p "$PLUGINS_DIR"
        chmod 755 "$PLUGINS_DIR"
    fi
    
    # Copy all plugin files
    for file in "$TEMP_DIR/plugins"/*; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            cp "$file" "$PLUGINS_DIR/$filename"
            chmod +x "$PLUGINS_DIR/$filename"
            log_message "Updated plugin: $filename"
        fi
    done
else
    log_message "Warning: plugins directory not found in repository."
fi

# Clean up temp directory
rm -rf "$TEMP_DIR"
log_message "Cleaned up temporary files."

# Restart the bot service
log_message "Restarting bot service..."
if /etc/init.d/revd restart; then
    log_message "Bot service restarted successfully."
else
    log_message "Failed to restart bot service. Try manually with: /etc/init.d/revd restart"
fi

log_message "Update process completed."
echo "
✅ Bot update completed!
Bot has been updated to the latest version from GitHub.
The service has been restarted automatically.
"
