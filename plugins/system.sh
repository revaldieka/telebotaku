#!/bin/sh

# Get system information
HOSTNAME=$(uci get system.@system[0].hostname 2>/dev/null || echo "Unknown")
# Set the model to Amlogic HG680P (S905X) as requested
MODEL="Amlogic HG680P (S905X)"
ARCH=$(uname -m)
FIRMWARE=$(cat /etc/openwrt_release 2>/dev/null | grep DISTRIB_DESCRIPTION | cut -d "'" -f 2 || echo "Unknown")
PLATFORM=$(cat /etc/openwrt_release 2>/dev/null | grep DISTRIB_TARGET | cut -d "'" -f 2 || echo "Unknown")
KERNEL=$(uname -r)
DATE=$(date +"%d %b %Y | %I:%M %p")
UPTIME=$(uptime | awk '{print $3,$4}' | sed 's/,//')
TEMP=$(awk '{printf "%.1f°C", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "N/A")
LOAD=$(awk '{printf "%.0f%%", $1 * 100}' /proc/loadavg)

# Fix CPU usage to only show percentage
CPU_RAW=$(top -bn1 | grep 'CPU:' | awk '{print $2}' || echo "N/A")
# Extract only the percentage and remove any trailing numbers
CPU=$(echo "$CPU_RAW" | grep -o "[0-9]*%" || echo "$CPU_RAW")

MEM_TOTAL=$(free | grep Mem | awk '{printf "%.1f MB", $2/1024}')
MEM_USED=$(free | grep Mem | awk '{printf "%.1f MB (%.0f%%)", $3/1024, $3*100/$2}')

# Create elegant report
cat << EOF

✦✦✦✦✦ SYSTEM MONITOR ✦✦✦✦✦

📡 Device: $HOSTNAME
🔧 Model: $MODEL
💻 System: $FIRMWARE
⚙️ Kernel: $KERNEL
🖥️ Arch: $ARCH Cortex-A53

⏱️ Uptime: $UPTIME
🌡️ Temp: $TEMP
📊 CPU: $CPU
📈 Load: $LOAD
🧠 Memory: $MEM_USED / $MEM_TOTAL

🕒 $DATE

✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF