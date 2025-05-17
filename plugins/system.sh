#!/bin/sh

#
# system monitor for OpenWRT
# REVD.CLOUD
uptime_str() { # <Time in Seconds>
    local Uptime=$1
    if [ $Uptime -gt 0 ]; then
        local Days=$(expr $Uptime / 60 / 60 / 24)
        local Hours=$(expr $Uptime / 60 / 60 % 24)
        local Minutes=$(expr $Uptime / 60 % 60)
        local Seconds=$(expr $Uptime % 60)
        if [ $Days -gt 0 ]; then
            Days=$(printf "%dd " $Days)
        else
            Days=""
        fi 2>/dev/null
        printf "$Days%02d:%02d:%02d" $Hours $Minutes $Seconds
    fi
}

# Get system information
HOSTNAME=$(uci get system.@system[0].hostname 2>/dev/null || echo "Unknown")
MODEL="Amlogic HG680P (S905X)"
ARCH=$(uname -m)
FIRMWARE=$(cat /etc/openwrt_release 2>/dev/null | grep DISTRIB_DESCRIPTION | cut -d "'" -f 2 || echo "Unknown")
PLATFORM=$(cat /etc/openwrt_release 2>/dev/null | grep DISTRIB_TARGET | cut -d "'" -f 2 || echo "Unknown")
KERNEL=$(uname -r)
DATE=$(date +"%d %b %Y | %I:%M %p")

# Better uptime formatting
SYS_UPTIME=$(cut -d. -f1 /proc/uptime)
UPTIME=$(uptime_str $SYS_UPTIME)

# System metrics
TEMP=$(awk '{printf "%.1f°C", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo "N/A")
LOAD=$(awk '{printf "%.0f%%", $1 * 100}' /proc/loadavg)

# Fix CPU usage to only show percentage
CPU_RAW=$(top -bn1 | grep 'CPU:' | awk '{print $2}' || echo "N/A")
CPU=$(echo "$CPU_RAW" | grep -o "[0-9]*%" || echo "$CPU_RAW")

MEM_TOTAL=$(free | grep Mem | awk '{printf "%.1f MB", $2/1024}')
MEM_USED=$(free | grep Mem | awk '{printf "%.1f MB (%.0f%%)", $3/1024, $3*100/$2}')

# Get network information
get_wan_info() {
    local wan_info=""
    local Zone
    local Device
    
    for Zone in $(uci -q show firewall | grep .masq= | cut -f2 -d.); do
        if [ "$(uci -q get firewall.$Zone.masq)" == "1" ]; then
            for Device in $(uci -q get firewall.$Zone.network); do
                local Status="$(ubus call network.interface.$Device status 2>/dev/null)"
                if [ "$Status" != "" ]; then
                    local State=""
                    local Iface=""
                    local IP4=""
                    local Subnet4=""
                    
                    # Parse JSON with jshn
                    . /usr/share/libubox/jshn.sh
                    json_load "${Status:-{}}"
                    json_get_var State up
                    json_get_var Iface l3_device
                    
                    if json_get_type Status ipv4_address && [ "$Status" = array ]; then
                        json_select ipv4_address
                        json_get_type Status 1
                        if [ "$Status" = object ]; then
                            json_select 1
                            json_get_var IP4 address
                            json_get_var Subnet4 mask
                            [ "$IP4" != "" ] && [ "$Subnet4" != "" ] && IP4="$IP4/$Subnet4"
                        fi
                    fi
                    
                    if [ "$State" == "1" ] && [ "$IP4" != "" ]; then
                        wan_info="$IP4 ($Iface)"
                        break 2
                    fi
                fi
            done
        fi
    done
    
    echo "$wan_info"
}

get_lan_info() {
    local lan_info=""
    local Zone
    local Device
    
    for Zone in $(uci -q show firewall | grep []]=zone | cut -f2 -d. | cut -f1 -d=); do
        if [ "$(uci -q get firewall.$Zone.masq)" != "1" ]; then
            for Device in $(uci -q get firewall.$Zone.network); do
                local Status="$(ubus call network.interface.$Device status 2>/dev/null)"
                if [ "$Status" != "" ]; then
                    local State=""
                    local Iface=""
                    local IP4=""
                    local Subnet4=""
                    
                    # Parse JSON with jshn
                    . /usr/share/libubox/jshn.sh
                    json_load "${Status:-{}}"
                    json_get_var State up
                    json_get_var Iface device
                    
                    if json_get_type Status ipv4_address && [ "$Status" = array ]; then
                        json_select ipv4_address
                        json_get_type Status 1
                        if [ "$Status" = object ]; then
                            json_select 1
                            json_get_var IP4 address
                            json_get_var Subnet4 mask
                            [ "$IP4" != "" ] && [ "$Subnet4" != "" ] && IP4="$IP4/$Subnet4"
                        fi
                    fi
                    
                    if [ "$IP4" != "" ]; then
                        if [ "$lan_info" != "" ]; then
                            lan_info="$lan_info, $IP4 ($Iface)"
                        else
                            lan_info="$IP4 ($Iface)"
                        fi
                    fi
                fi
            done
        fi
    done
    
    echo "$lan_info"
}

get_br_lan_info() {
    local br_info=""
    if [ -e /sys/class/net/br-lan ]; then
        local IP=$(ip -4 addr show br-lan | grep -oP '(?<=inet\s)\d+(\.\d+){3}\/\d+' | head -n 1)
        if [ -n "$IP" ]; then
            br_info="$IP (br-lan)"
        fi
    fi
    echo "$br_info"
}

get_wlan_info() {
    local wlan_info=""
    local Iface
    
    for Iface in $(uci -q show wireless | grep device=radio | cut -f2 -d.); do
        local Device=$(uci -q get wireless.$Iface.device)
        local SSID=$(uci -q get wireless.$Iface.ssid)
        local IfaceDisabled=$(uci -q get wireless.$Iface.disabled)
        local DeviceDisabled=$(uci -q get wireless.$Device.disabled)
        
        if [ -n "$SSID" ] && [ "$IfaceDisabled" != "1" ] && [ "$DeviceDisabled" != "1" ]; then
            local Mode=$(uci -q -P /var/state get wireless.$Iface.mode)
            local Channel=$(uci -q get wireless.$Device.channel)
            local RadioIface=$(uci -q -P /var/state get wireless.$Iface.ifname)
            
            if [ -n "$RadioIface" ]; then
                if [ "$Mode" == "ap" ]; then
                    local Connections=$(iw dev $RadioIface station dump | grep Station | wc -l 2>/dev/null)
                    wlan_info="$SSID ($Mode), ch: $Channel, conn: $Connections"
                else
                    local Connection=$(iw dev $RadioIface link | awk 'BEGIN{FS=": ";Signal="";Bitrate=""} $1~/signal/ {Signal=$2} $1~/tx bitrate/ {Bitrate=$2}END{print Signal" "Bitrate}' 2>/dev/null)
                    wlan_info="$SSID ($Mode), ch: $Channel, $Connection"
                fi
                break
            fi
        fi
    done
    
    echo "$wlan_info"
}

# Get network information
WAN_INFO=$(get_wan_info)
LAN_INFO=$(get_lan_info)
BR_LAN_INFO=$(get_br_lan_info)
WLAN_INFO=$(get_wlan_info)

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

🌐 Network Information:
   WAN: ${WAN_INFO:-Not detected}
   LAN: ${LAN_INFO:-Not detected}

🕒 $DATE

✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦
  Telegram: t.me/ValltzID
  Instagram: revd.cloud
✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦
EOF
