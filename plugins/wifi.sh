#!/bin/sh

# OpenWRT WiFi Information Script
# REVD.CLOUD

echo ""
echo "  ✦✦✦✦✦ WIFI INFORMATION ✦✦✦✦✦"
echo ""

# Get WiFi interfaces
wifi_found=0

# Check each radio
for radio in $(uci show wireless | grep "wireless\.radio" | cut -d. -f2 | cut -d= -f1 | sort -u); do
    if [ "$radio" != "radio" ]; then
        # Get radio info
        channel=$(uci get wireless.$radio.channel 2>/dev/null || echo "auto")
        band=$(uci get wireless.$radio.band 2>/dev/null || echo "unknown")
        htmode=$(uci get wireless.$radio.htmode 2>/dev/null || echo "unknown")
        disabled=$(uci get wireless.$radio.disabled 2>/dev/null || echo "0")
        
        if [ "$disabled" = "1" ]; then
            status="🔴 DISABLED"
        else
            status="🟢 ENABLED"
        fi
        
        echo "  📡 Radio: $radio"
        echo "     Status: $status"
        echo "     Band: $band"
        echo "     Channel: $channel"
        echo "     Mode: $htmode"
        echo ""
        
        wifi_found=1
    fi
done

# Get WiFi networks
echo "  🌐 WiFi Networks:"
network_count=0

for iface in $(uci show wireless | grep "wireless\.@wifi-iface" | cut -d. -f2 | cut -d= -f1 | sort -u); do
    ssid=$(uci get wireless.$iface.ssid 2>/dev/null)
    mode=$(uci get wireless.$iface.mode 2>/dev/null || echo "ap")
    encryption=$(uci get wireless.$iface.encryption 2>/dev/null || echo "none")
    disabled=$(uci get wireless.$iface.disabled 2>/dev/null || echo "0")
    device=$(uci get wireless.$iface.device 2>/dev/null)
    
    if [ -n "$ssid" ]; then
        network_count=$((network_count + 1))
        
        if [ "$disabled" = "1" ]; then
            net_status="🔴 DISABLED"
        else
            net_status="🟢 ACTIVE"
        fi
        
        # Get connected clients for AP mode
        if [ "$mode" = "ap" ] && [ "$disabled" != "1" ]; then
            # Try to get interface name
            ifname=$(uci get wireless.$iface.ifname 2>/dev/null)
            if [ -z "$ifname" ]; then
                # Generate likely interface name
                ifname="wlan0"
                if [ "$device" = "radio1" ]; then
                    ifname="wlan1"
                fi
            fi
            
            # Count connected stations
            if [ -d "/sys/class/net/$ifname" ]; then
                clients=$(iw dev $ifname station dump 2>/dev/null | grep "Station" | wc -l)
            else
                clients="N/A"
            fi
        else
            clients="N/A"
        fi
        
        echo "     • SSID: $ssid"
        echo "       Status: $net_status"
        echo "       Mode: $mode"
        echo "       Security: $encryption"
        echo "       Radio: $device"
        if [ "$mode" = "ap" ]; then
            echo "       Clients: $clients"
        fi
        echo ""
        
        wifi_found=1
    fi
done

if [ $wifi_found -eq 0 ]; then
    echo "     • No WiFi interfaces found"
    echo ""
fi

# Get WiFi statistics if available
echo "  📊 WiFi Statistics:"
for iface in wlan0 wlan1; do
    if [ -d "/sys/class/net/$iface" ]; then
        rx_bytes=$(cat /sys/class/net/$iface/statistics/rx_bytes 2>/dev/null)
        tx_bytes=$(cat /sys/class/net/$iface/statistics/tx_bytes 2>/dev/null)
        
        if [ -n "$rx_bytes" ] && [ -n "$tx_bytes" ]; then
            # Convert to MB
            rx_mb=$((rx_bytes / 1024 / 1024))
            tx_mb=$((tx_bytes / 1024 / 1024))
            
            echo "     • $iface: RX ${rx_mb}MB, TX ${tx_mb}MB"
        fi
    fi
done

echo ""
echo "  ✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦"
echo "  Telegram: t.me/ValltzID"
echo "  Instagram: revd.cloud"
echo "  ✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦"
echo ""