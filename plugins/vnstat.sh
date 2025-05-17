#!/bin/sh

# Check if vnstat is installed
if ! command -v vnstat >/dev/null 2>&1; then
    cat << EOF

  ✦✦✦✦✦ NETWORK STATS ✦✦✦✦✦

  ⚠️  vnstat is not installed. Please install it:
      opkg update && opkg install vnstat

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Use only br-lan interface
INTERFACE="br-lan"

# Check if br-lan exists
if [ ! -d "/sys/class/net/$INTERFACE" ]; then
    cat << EOF

  ✦✦✦✦✦ NETWORK STATS ✦✦✦✦✦

  ⚠️  Interface $INTERFACE not found

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Ensure vnstat database exists for the interface
vnstat -i "$INTERFACE" -u >/dev/null 2>&1

# Check if vnstat database is ready
if ! vnstat -i "$INTERFACE" > /dev/null 2>&1; then
    cat << EOF

  ✦✦✦✦✦ NETWORK STATS ✦✦✦✦✦

  ⚠️  Could not get vnstat data for interface $INTERFACE
  
  Database created. Please wait a few minutes for data collection.
  
  Run this command again later after vnstat has collected some data.
  
  You can check vnstat status with:
  vnstat -i $INTERFACE

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    # Try to create the database
    vnstat -i "$INTERFACE" --create >/dev/null 2>&1
    exit 1
fi

# Get today's usage data
get_daily_usage() {
    # Get the current date line from vnstat daily output
    # Using --style 0 for simpler parsing
    TODAY_LINE=$(vnstat -i "$INTERFACE" -d --style 0 | grep "$(date +"%Y-%m-%d")")
    
    if [ -n "$TODAY_LINE" ]; then
        # Fix: Switch positions to correct RX/TX
        TODAY_RX=$(echo "$TODAY_LINE" | awk '{print $5 " " $6}')
        TODAY_TX=$(echo "$TODAY_LINE" | awk '{print $2 " " $3}')
        TODAY_TOTAL=$(echo "$TODAY_LINE" | awk '{print $8 " " $9}')
    else
        # Try alternative format for today (may show as "today")
        TODAY_LINE=$(vnstat -i "$INTERFACE" -d --style 0 | grep "today")
        
        if [ -n "$TODAY_LINE" ]; then
            # Fix: Switch positions for "today" format too
            TODAY_RX=$(echo "$TODAY_LINE" | awk '{print $5 " " $6}')
            TODAY_TX=$(echo "$TODAY_LINE" | awk '{print $2 " " $3}')
            TODAY_TOTAL=$(echo "$TODAY_LINE" | awk '{print $8 " " $9}')
        else
            TODAY_RX="0 KiB"
            TODAY_TX="0 KiB"
            TODAY_TOTAL="0 KiB"
        fi
    fi
    
    echo "$TODAY_RX;$TODAY_TX;$TODAY_TOTAL"
}

# Get monthly usage as provided by user
get_monthly_usage() {
    # Get the current month from vnstat
    MONTH_LINE=$(vnstat -i "$INTERFACE" -m 1 --style 0 | sed -n 6p)
    
    if [ -n "$MONTH_LINE" ]; then
        # Keep original columns as they were already correct
        MONTH_RX=$(echo "$MONTH_LINE" | awk '{print $5 " " $6}')
        MONTH_TX=$(echo "$MONTH_LINE" | awk '{print $2 " " $3}')
        MONTH_TOTAL=$(echo "$MONTH_LINE" | awk '{print $8 " " $9}')
    else
        MONTH_RX="0 KiB"
        MONTH_TX="0 KiB"
        MONTH_TOTAL="0 KiB"
    fi
    
    echo "$MONTH_RX;$MONTH_TX;$MONTH_TOTAL"
}

# Get all-time total usage
get_total_usage() {
    # Get the total line from vnstat summary
    TOTAL_LINE=$(vnstat -i "$INTERFACE" --style 0 | grep "total")
    
    if [ -n "$TOTAL_LINE" ]; then
        TOTAL_RX=$(echo "$TOTAL_LINE" | awk '{print $2 " " $3}')
        TOTAL_TX=$(echo "$TOTAL_LINE" | awk '{print $5 " " $6}')
        TOTAL_SUM=$(echo "$TOTAL_LINE" | awk '{print $8 " " $9}')
    else
        TOTAL_RX="0 KiB"
        TOTAL_TX="0 KiB"
        TOTAL_SUM="0 KiB"
    fi
    
    echo "$TOTAL_RX;$TOTAL_TX;$TOTAL_SUM"
}

# Get all the usage data
DAILY_DATA=$(get_daily_usage)
MONTHLY_DATA=$(get_monthly_usage)
TOTAL_DATA=$(get_total_usage)

# Parse the data
TODAY_RX=$(echo "$DAILY_DATA" | cut -d';' -f1)
TODAY_TX=$(echo "$DAILY_DATA" | cut -d';' -f2)
TODAY_TOTAL=$(echo "$DAILY_DATA" | cut -d';' -f3)

MONTH_RX=$(echo "$MONTHLY_DATA" | cut -d';' -f1)
MONTH_TX=$(echo "$MONTHLY_DATA" | cut -d';' -f2)
MONTH_TOTAL=$(echo "$MONTHLY_DATA" | cut -d';' -f3)

TOTAL_RX=$(echo "$TOTAL_DATA" | cut -d';' -f1)
TOTAL_TX=$(echo "$TOTAL_DATA" | cut -d';' -f2)
TOTAL_SUM=$(echo "$TOTAL_DATA" | cut -d';' -f3)

# Format report
cat << EOF

  ✦✦✦✦✦ NETWORK STATS ✦✦✦✦✦

  📡 Interface: $INTERFACE

  TODAY:
  ↓ Download: $TODAY_RX 
  ↑ Upload:   $TODAY_TX
  ∑ Total:    $TODAY_TOTAL

  THIS MONTH:
  ↓ Download: $MONTH_RX
  ↑ Upload:   $MONTH_TX
  ∑ Total:    $MONTH_TOTAL

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦
  Telegram: @ValltzID
  Instagram: revd.cloud
  ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦

EOF
