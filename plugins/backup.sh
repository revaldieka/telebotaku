#!/bin/sh

# OpenWRT Configuration Backup Script
# REVD.CLOUD

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    cat << EOF

  ✦✦✦✦✦ BACKUP SYSTEM ✦✦✦✦✦

  ⚠️  Access denied
  This script must run as root

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Create backup directory
BACKUP_DIR="/tmp/openwrt_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating system backup..."

# Backup system configuration
echo "📁 Backing up system configuration..."
sysupgrade -b "$BACKUP_DIR/system_config.tar.gz" 2>/dev/null

# Backup network configuration
echo "🌐 Backing up network settings..."
cp -r /etc/config "$BACKUP_DIR/config_backup" 2>/dev/null

# Backup bot configuration
echo "🤖 Backing up bot configuration..."
if [ -d "/root/REVDBOT" ]; then
    cp -r /root/REVDBOT "$BACKUP_DIR/bot_backup" 2>/dev/null
    # Remove sensitive session files
    rm -f "$BACKUP_DIR/bot_backup/bot_session.session" 2>/dev/null
fi

# Backup crontab
echo "⏰ Backing up scheduled tasks..."
crontab -l > "$BACKUP_DIR/crontab_backup.txt" 2>/dev/null

# Backup installed packages list
echo "📦 Backing up package list..."
opkg list-installed > "$BACKUP_DIR/installed_packages.txt" 2>/dev/null

# Create backup info file
cat > "$BACKUP_DIR/backup_info.txt" << EOF
OpenWRT Backup Information
=========================
Backup Date: $(date)
Hostname: $(uci get system.@system[0].hostname 2>/dev/null || echo "Unknown")
OpenWRT Version: $(cat /etc/openwrt_release 2>/dev/null | grep DISTRIB_DESCRIPTION | cut -d "'" -f 2 || echo "Unknown")
Kernel Version: $(uname -r)
Architecture: $(uname -m)

Backup Contents:
- System configuration (system_config.tar.gz)
- Network configuration (config_backup/)
- Bot configuration (bot_backup/)
- Crontab (crontab_backup.txt)
- Installed packages (installed_packages.txt)

Restore Instructions:
1. For system config: sysupgrade -r system_config.tar.gz
2. For network config: copy files from config_backup/ to /etc/config/
3. For bot config: copy bot_backup/ to /root/REVDBOT/
4. For crontab: crontab crontab_backup.txt
EOF

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

# Create compressed archive
echo "🗜️ Compressing backup..."
cd /tmp
tar -czf "openwrt_backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$(basename "$BACKUP_DIR")" 2>/dev/null
ARCHIVE_NAME="openwrt_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

# Clean up temporary directory
rm -rf "$BACKUP_DIR"

# Get final archive size
ARCHIVE_SIZE=$(du -sh "/tmp/$ARCHIVE_NAME" | cut -f1)

# Format report
cat << EOF

  ✦✦✦✦✦ BACKUP COMPLETE ✦✦✦✦✦

  ✅ Backup created successfully

  📊 Backup Details:
     • Archive: $ARCHIVE_NAME
     • Size: $ARCHIVE_SIZE
     • Location: /tmp/$ARCHIVE_NAME
     • Created: $(date)

  📋 Backup Contents:
     • System configuration
     • Network settings
     • Bot configuration
     • Scheduled tasks
     • Package list

  💡 Note: Archive will be deleted on reboot
     Download it now if needed!

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦
  Telegram: t.me/ValltzID
  Instagram: revd.cloud
  ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦

EOF