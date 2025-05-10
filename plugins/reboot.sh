#!/bin/sh

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    cat << EOF

  ✦✦✦✦✦ SYSTEM REBOOT ✦✦✦✦✦

  ⚠️  Permission Error
  This script must run as root

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Get system information
HOSTNAME=$(uci get system.@system[0].hostname 2>/dev/null || echo "Device")
UPTIME=$(uptime | awk '{print $3,$4}' | sed 's/,//')

# Format report
cat << EOF

  ✦✦✦✦✦ SYSTEM REBOOT ✦✦✦✦✦

  🔄 Rebooting: $HOSTNAME
  ⏱️  Current Uptime: $UPTIME

  The device will be offline for
  approximately 1-2 minutes.

  Please reconnect after reboot.

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF

# Sync filesystem before reboot
sync

# Reboot with timeout to ensure the message is displayed
(sleep 3 && reboot) &