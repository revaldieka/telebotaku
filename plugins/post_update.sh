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
