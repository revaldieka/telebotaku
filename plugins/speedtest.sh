#!/bin/sh

# Check if speedtest-cli is installed
if ! command -v speedtest-cli >/dev/null 2>&1; then
    cat << EOF

  ✦✦✦✦✦ SPEED TEST ✦✦✦✦✦

  ⚠️  speedtest-cli is not installed

  Please install it using:
  opkg update
  opkg install python3-speedtest-cli

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

# Run speedtest with timeout (some OpenWRT devices need this)
timeout 120 speedtest-cli --simple > /tmp/speedtest_result 2>/dev/null
SPEEDTEST_STATUS=$?

if [ $SPEEDTEST_STATUS -ne 0 ]; then
    cat << EOF

  ✦✦✦✦✦ SPEED TEST ✦✦✦✦✦

  ⚠️  Speed test failed

  Please check your network
  connection and try again later.

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦

EOF
    exit 1
fi

SPEEDTEST_RESULT=$(cat /tmp/speedtest_result)
rm -f /tmp/speedtest_result

# Extract values
PING=$(echo "$SPEEDTEST_RESULT" | grep "Ping" | awk '{print $2}')
DOWNLOAD=$(echo "$SPEEDTEST_RESULT" | grep "Download" | awk '{print $2}')
UPLOAD=$(echo "$SPEEDTEST_RESULT" | grep "Upload" | awk '{print $2}')

# Get ISP info (try multiple methods)
get_isp() {
    # Try ifconfig.co first
    ISP=$(curl -s --connect-timeout 5 ifconfig.co/json 2>/dev/null | grep -o '"org":"[^"]*"' | cut -d'"' -f4)
    
    # If that fails, try ipinfo.io
    if [ -z "$ISP" ]; then
        ISP=$(curl -s --connect-timeout 5 ipinfo.io 2>/dev/null | grep '"org"' | cut -d'"' -f4)
    fi
    
    # If still empty, try whoami.akamai.net
    if [ -z "$ISP" ]; then
        ISP=$(curl -s --connect-timeout 5 https://whoami.akamai.net 2>/dev/null | grep -o '"group":"[^"]*"' | cut -d'"' -f4)
    fi
    
    # Default value if all methods fail
    if [ -z "$ISP" ]; then
        ISP="Unknown"
    fi
    
    echo "$ISP"
}

ISP=$(get_isp)

# Add quality rating - replace bc with awk
if awk "BEGIN {exit !($DOWNLOAD >= 100)}"; then
    RATING="Excellent ★★★★★"
elif awk "BEGIN {exit !($DOWNLOAD >= 50)}"; then
    RATING="Good ★★★★☆"
elif awk "BEGIN {exit !($DOWNLOAD >= 25)}"; then
    RATING="Fair ★★★☆☆"
elif awk "BEGIN {exit !($DOWNLOAD >= 10)}"; then
    RATING="Basic ★★☆☆☆"
else
    RATING="Poor ★☆☆☆☆"
fi

# Format report
cat << EOF

  ✦✦✦✦✦ SPEED TEST ✦✦✦✦✦

  📡 ISP: $ISP

  ↓ Download: $DOWNLOAD Mbps
  ↑ Upload:   $UPLOAD Mbps
  📊 Ping:     $PING ms

  Test provided by speedtest.net

  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦
    Telegram: t.me/ValltzID
  Instagram: revd.cloud
  ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦

EOF
