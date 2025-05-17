#!/bin/sh

#
# User List
# REVD.CLOUD
#

# Function to determine device type icon based on MAC vendor
get_device_icon() {
    local mac=$1
    local vendor=$(echo $mac | cut -d':' -f1-3 | tr 'a-z' 'A-Z')
    
    case "$vendor" in
        "00:50:56"|"00:0C:29"|"00:05:69"|"00:1C:14"|"00:1C:42")
            echo "💻" # VMware/PC
            ;;
        "3C:22:FB"|"58:FB:84"|"AC:87:A3"|"28:CF:DA"|"04:D3:B0"|"34:2C:C4"|"98:01:A7"|"68:FB:7E"|"90:B0:ED"|"D4:38:9C")
            echo "📱" # Apple
            ;;
        "00:16:41"|"22:21:E9"|"C2:9F:DB")
            echo "📺" # Smart TV
            ;;
        "DC:A6:32"|"B8:27:EB"|"E4:5F:01")
            echo "🍓" # Raspberry Pi
            ;;
        *)
            echo "🖥️" # Generic device
            ;;
    esac
}

# Function to get the hostname from IP
get_hostname() {
    local ip=$1
    local hostname=$(grep -E "^$ip " /tmp/hosts/dhcp 2>/dev/null | awk '{print $2}')
    
    if [ -z "$hostname" ]; then
        hostname=$(grep " $ip$" /etc/hosts 2>/dev/null | awk '{print $2}')
    fi
    
    echo $hostname
}

# Print header
print_header() {
    echo "✦✦✦✦✦ CONNECTED USERS ✦✦✦✦✦"
    # Count connected devices from DHCP leases only
    local dhcp_count=0
    if [ -f "/tmp/dhcp.leases" ]; then
        dhcp_count=$(wc -l < /tmp/dhcp.leases)
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 Total Devices: $dhcp_count"
}

# Get DHCP leases
process_dhcp_leases() {
    if [ -f "/tmp/dhcp.leases" ]; then
        # Counter for devices
        local count=0
        local current_time=$(date +%s)
        
        while IFS=' ' read -r lease_time mac ip hostname _; do
            # Skip empty hostnames or MAC addresses
            [ -z "$mac" ] || [ "$mac" = "*" ] && continue
            
            count=$((count+1))
            
            # Get device icon
            icon=$(get_device_icon $mac)
            
            # If hostname is * or empty, try to get from hosts file
            if [ -z "$hostname" ] || [ "$hostname" = "*" ]; then
                hostname=$(get_hostname $ip)
                [ -z "$hostname" ] && hostname="unknown"
            fi
            
            # Truncate hostname if too long
            if [ ${#hostname} -gt 20 ]; then
                hostname="${hostname:0:20}..."
            fi
            
            # Calculate lease time remaining
            lease_remaining=$((lease_time - current_time))
            if [ $lease_remaining -le 0 ]; then
                lease_remaining_str="Expired"
            else
                # Convert to hours and minutes
                hours=$((lease_remaining / 3600))
                minutes=$(((lease_remaining % 3600) / 60))
                lease_remaining_str="${hours}h ${minutes}m"
            fi
            
            # Print each device in a simple list format
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "Perangkat $count $icon"
            echo "IP: $ip"
            echo "Hostname: $hostname"
            echo "MAC: $mac"
            echo "Lease Time: $lease_remaining_str"
            echo ""
        done < /tmp/dhcp.leases
    else
        echo "No DHCP leases found."
    fi
}

# Main function
main() {
    print_header
    
    # Process DHCP leases only
    process_dhcp_leases
    
    # Add footer
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦"
    echo " Telegram: @ValltzID"
    echo " Instagram: revd.cloud"
    echo "✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦✦" 
}

# Run the main function
main
