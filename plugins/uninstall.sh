#!/bin/sh

# Enhanced OpenWRT Telegram Bot Uninstaller
# REVD.CLOUD

# Get the keep_config parameter
keep_config=$1

echo "
╔═══════════════════════════════════╗
║  OpenWRT Telegram Bot Uninstaller ║
║            REVD.CLOUD             ║
╚═══════════════════════════════════╝
"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "⚠️  This script requires root access."
    echo "Please run with 'sudo' or as root."
    exit 1
fi

# Define paths
INIT_SCRIPT="/etc/init.d/revd"
ROOT_DIR="/root/REVDBOT"
SERVICE_NAME="revd"
BACKUP_DIR="/etc/revd_backup"
LOG_FILE="/var/log/revd_bot.log"

echo "🔍 Checking bot installation..."

# Check if service exists
if [ ! -f "$INIT_SCRIPT" ]; then
    echo "❌ Bot service not found in system."
    echo "It seems the bot was never installed or already removed."
    
    # Still check for remnant directories
    if [ -d "$ROOT_DIR" ]; then
        echo "📁 However, bot directory found. Continuing cleanup..."
    else
        echo "📁 Searching for installation remnants..."
    fi
else
    echo "✅ Bot service found in system."
fi

echo "🛑 Stopping bot service..."
if [ -f "$INIT_SCRIPT" ]; then
    # Stop the service
    $INIT_SCRIPT stop
    
    # Disable the service
    $INIT_SCRIPT disable
    
    echo "🗑️  Removing init script..."
    # Remove the init script
    rm -f "$INIT_SCRIPT"
else
    echo "ℹ️  Service not found, continuing to next step."
fi

# Kill any remaining bot processes
echo "🔍 Finding and stopping remaining bot processes..."
BOT_PIDS=$(ps | grep "bot_openwrt.py" | grep -v grep | awk '{print $1}')
if [ -n "$BOT_PIDS" ]; then
    echo "🛑 Stopping bot processes with PID: $BOT_PIDS"
    kill -9 $BOT_PIDS 2>/dev/null
else
    echo "ℹ️  No bot processes running."
fi

# Handle configuration based on parameter
if [ "$keep_config" = "y" ]; then
    # Create backup directory if it doesn't exist
    if [ ! -d "/etc/revd_backup" ]; then
        mkdir -p "/etc/revd_backup"
    fi
    
    # Backup configuration
    if [ -f "$ROOT_DIR/config.ini" ]; then
        echo "💾 Saving configuration backup to /etc/revd_backup/config.ini"
        cp "$ROOT_DIR/config.ini" "/etc/revd_backup/config.ini"
        chmod 600 "/etc/revd_backup/config.ini"
    fi
    
    # Backup plugins
    if [ -d "$ROOT_DIR/plugins" ]; then
        echo "💾 Saving plugins backup to /etc/revd_backup/plugins/"
        mkdir -p "/etc/revd_backup/plugins"
        cp -r "$ROOT_DIR/plugins/"* "/etc/revd_backup/plugins/" 2>/dev/null
        chmod +x "/etc/revd_backup/plugins/"*.sh 2>/dev/null
    fi
    
    # Create restoration script
    cat > "/etc/revd_backup/restore.sh" << 'EOF'
#!/bin/sh
# Bot restoration script
echo "Restoring REVD Bot configuration..."

# Download and run installer
cd /tmp
curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh
chmod +x revd_installer.sh

# Restore config after installation
if [ -f "/etc/revd_backup/config.ini" ]; then
    echo "Restoring configuration..."
    cp /etc/revd_backup/config.ini /root/REVDBOT/config.ini
fi

# Restore plugins
if [ -d "/etc/revd_backup/plugins" ]; then
    echo "Restoring plugins..."
    cp -r /etc/revd_backup/plugins/* /root/REVDBOT/plugins/
    chmod +x /root/REVDBOT/plugins/*.sh
fi

echo "Restoration complete. Starting bot..."
/etc/init.d/revd restart
EOF
    chmod +x "/etc/revd_backup/restore.sh"
    
    echo "✅ Backup completed."
    echo "💡 To restore later, run: /etc/revd_backup/restore.sh"
else
    # Remove backup directory if it exists
    if [ -d "$BACKUP_DIR" ]; then
        echo "🗑️  Removing backup directory..."
        rm -rf "$BACKUP_DIR"
    fi
fi

# Remove bot directory
echo "🗑️  Removing bot directory at $ROOT_DIR..."
if [ -d "$ROOT_DIR" ]; then
    rm -rf "$ROOT_DIR"
    echo "✅ Bot directory successfully removed."
else
    echo "ℹ️  Bot directory not found."
fi

# Remove log file
if [ -f "$LOG_FILE" ]; then
    echo "🗑️  Removing log file..."
    rm -f "$LOG_FILE"
fi

# Remove startup symlink if exists
STARTUP_LINK="/etc/rc.d/S99$SERVICE_NAME"
if [ -L "$STARTUP_LINK" ]; then
    echo "🗑️  Removing startup symlink..."
    rm -f "$STARTUP_LINK"
fi

# Clean up any remaining rc.d entries
for RCLINK in /etc/rc.d/*$SERVICE_NAME; do
    if [ -L "$RCLINK" ]; then
        echo "🗑️  Removing symlink $RCLINK..."
        rm -f "$RCLINK"
    fi
done

# Remove session files
echo "🗑️  Cleaning up session files..."
rm -f /root/bot_session.session* 2>/dev/null

echo ""
echo "✅ Uninstall completed successfully!"
echo ""

if [ "$keep_config" = "y" ]; then
    echo "💾 Configuration backed up to: /etc/revd_backup/"
    echo "🔄 To reinstall with saved config: /etc/revd_backup/restore.sh"
    echo ""
fi

echo "🚀 Thank you for using REVD.CLOUD services!"
echo "    To reinstall in the future, use:"
echo "    opkg update && (cd /tmp && curl -sLko revd_installer.sh https://raw.githubusercontent.com/revaldieka/telebotaku/main/revd_installer.sh && chmod +x revd_installer.sh && sh revd_installer.sh)"
echo ""
echo "📱 Contact: t.me/ValltzID"
echo "🌐 Website: revd.cloud"