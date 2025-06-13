#!/bin/sh

# OpenWRT Firewall Status Script
# REVD.CLOUD

echo ""
echo "  ✦✦✦✦✦ FIREWALL STATUS ✦✦✦✦✦"
echo ""

# Check if firewall is running
if pgrep -f "firewall" > /dev/null; then
    FIREWALL_STATUS="🟢 ACTIVE"
else
    FIREWALL_STATUS="🔴 INACTIVE"
fi

echo "  🔥 Firewall: $FIREWALL_STATUS"
echo ""

# Get firewall zones
echo "  🌐 Firewall Zones:"
uci show firewall | grep "firewall\.@zone\[" | while read line; do
    zone_index=$(echo "$line" | grep -o "\[.*\]" | tr -d "[]")
    zone_name=$(uci get firewall.@zone[$zone_index].name 2>/dev/null)
    zone_input=$(uci get firewall.@zone[$zone_index].input 2>/dev/null)
    zone_output=$(uci get firewall.@zone[$zone_index].output 2>/dev/null)
    zone_forward=$(uci get firewall.@zone[$zone_index].forward 2>/dev/null)
    
    if [ -n "$zone_name" ]; then
        echo "     • $zone_name: IN=$zone_input OUT=$zone_output FWD=$zone_forward"
    fi
done

echo ""

# Get active rules count
RULES_COUNT=$(iptables -L | grep -c "^Chain\|^target")
echo "  📊 Active Rules: $RULES_COUNT"

# Check for port forwards
echo ""
echo "  🔄 Port Forwards:"
FORWARDS=$(uci show firewall | grep "firewall\.@redirect" | wc -l)
if [ "$FORWARDS" -gt 0 ]; then
    echo "     • $FORWARDS port forward(s) configured"
    uci show firewall | grep "firewall\.@redirect" | head -5 | while read line; do
        redirect_index=$(echo "$line" | grep -o "\[.*\]" | tr -d "[]" | head -1)
        if [ -n "$redirect_index" ]; then
            src_port=$(uci get firewall.@redirect[$redirect_index].src_dport 2>/dev/null)
            dest_ip=$(uci get firewall.@redirect[$redirect_index].dest_ip 2>/dev/null)
            dest_port=$(uci get firewall.@redirect[$redirect_index].dest_port 2>/dev/null)
            if [ -n "$src_port" ] && [ -n "$dest_ip" ]; then
                echo "     • Port $src_port → $dest_ip:$dest_port"
            fi
        fi
    done
else
    echo "     • No port forwards configured"
fi

echo ""

# Check for blocked IPs (if any)
BLOCKED_IPS=$(iptables -L INPUT | grep "DROP" | wc -l)
echo "  🚫 Blocked Connections: $BLOCKED_IPS"

# Get connection tracking info
CONNTRACK_COUNT=$(cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null || echo "N/A")
CONNTRACK_MAX=$(cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null || echo "N/A")

echo "  🔗 Connection Tracking: $CONNTRACK_COUNT / $CONNTRACK_MAX"

echo ""
echo "  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦"
echo "  Telegram: t.me/ValltzID"
echo "  Instagram: revd.cloud"
echo "  ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦"
echo ""