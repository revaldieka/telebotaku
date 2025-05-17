#!/bin/sh

# Define default target if none is specified
TARGET=${1:-"google.com"}
PING_COUNT=4

# Always ensure there's some output
echo ""
echo "  ✦✦✦✦✦ NETWORK TEST ✦✦✦✦✦"
echo ""
echo "  📡 Testing connection to $TARGET..."

# Run ping test with timeout
ping_result=$(ping -c $PING_COUNT -W 2 "$TARGET" 2>&1)
ping_status=$?

# Make sure we have output even if ping fails
if [ $ping_status -eq 0 ]; then
    # Extract ping statistics
    avg_ping=$(echo "$ping_result" | grep "min/avg/max" | awk -F'/' '{printf "%.0f", $5}')
    packet_loss=$(echo "$ping_result" | grep "packet loss" | awk -F',' '{print $3}' | awk '{print $1}')
    
    # Format quality rating
    if [ "$avg_ping" -lt 50 ]; then
        quality="Excellent ★★★★★ ($avg_ping ms)"
    elif [ "$avg_ping" -lt 100 ]; then
        quality="Good ★★★★☆ ($avg_ping ms)"
    elif [ "$avg_ping" -lt 150 ]; then
        quality="Fair ★★★☆☆ ($avg_ping ms)"
    elif [ "$avg_ping" -lt 200 ]; then
        quality="Poor ★★☆☆☆ ($avg_ping ms)"
    else
        quality="Very Poor ★☆☆☆☆ ($avg_ping ms)"
    fi
    
    echo ""
    echo "  🌐 PING: $quality"
    echo "  📊 Packet Loss: $packet_loss"
    echo ""
    echo "  ✅ CONNECTION STATUS: ONLINE"
else
    echo ""
    echo "  ❌ $TARGET: Connection failed"
    echo ""
    echo "  ⚠️ CONNECTION STATUS: OFFLINE"
    echo "  💡 Suggestion: Check your internet connection"
fi

echo ""
echo " ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦"
echo " Telegram: t.me/ValltzID"
echo " Instagram: revd.cloud"
echo " ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦"
echo ""

# Always ensure we have output
if [ -z "$ping_result" ]; then
    echo "  Error: Unable to complete ping test."
    echo "  Please try again later."
fi
