#!/bin/sh

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    cat << EOF

  ✦✦✦✦✦ MEMORY CLEANER ✦✦✦✦✦

  ⚠️  Permission Error
  This script must run as root

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Get total memory
TOTAL_MEM=$(free | grep "Mem:" | awk '{printf "%.2f", $2/1024}')

# Get free memory before clearing
BEFORE=$(free | grep "Mem:" | awk '{printf "%.2f", $4/1024}')
BEFORE_PERCENT=$(free | grep "Mem:" | awk '{printf "%.1f", $4*100/$2}')

echo "Clearing memory cache... Please wait"

# Clear RAM cache (more thorough approach)
sync
echo 1 > /proc/sys/vm/drop_caches
sleep 1
echo 2 > /proc/sys/vm/drop_caches
sleep 1
echo 3 > /proc/sys/vm/drop_caches

# Get free memory after clearing
AFTER=$(free | grep "Mem:" | awk '{printf "%.2f", $4/1024}')
AFTER_PERCENT=$(free | grep "Mem:" | awk '{printf "%.1f", $4*100/$2}')

# Calculate freed memory - using awk for better floating point handling
FREED_MB=$(awk -v after="$AFTER" -v before="$BEFORE" 'BEGIN {printf "%.2f", after - before}')

# Format the report
cat << EOF

  ✦✦✦✦✦ MEMORY CLEANER ✦✦✦✦✦

  ✅ RAM cleared successfully

  📊 Memory Status:
     • Before: $BEFORE MB ($BEFORE_PERCENT%)
     • After:  $AFTER MB ($AFTER_PERCENT%)
     • Freed:  $FREED_MB MB

  💻 Total Memory: $TOTAL_MEM MB

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
