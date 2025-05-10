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
    echo ""
    echo "✦✦✦✦✦ CONNECTED USERS ✦✦✦✦✦"
    echo ""
    # Count connected devices
    local dhcp_count=0
    local arp_count=0
    if [ -f "/tmp/dhcp.leases" ]; then
        dhcp_count=$(wc -l < /tmp/dhcp.leases)
    fi
    arp_count=$(ip neigh show | grep -v FAILED | wc -l)
    echo "📊 Total Devices: $(($dhcp_count + $arp_count))"
    echo ""
}

# Get DHCP leases
process_dhcp_leases() {
    if [ -f "/tmp/dhcp.leases" ]; then
        while IFS=' ' read -r lease_time mac ip hostname _; do
            # Skip empty hostnames or MAC addresses
            [ -z "$mac" ] || [ "$mac" = "*" ] && continue
            
            # Get device icon
            icon=$(get_device_icon $mac)
            
            # If hostname is * or empty, try to get from hosts file
            if [ -z "$hostname" ] || [ "$hostname" = "*" ]; then
                hostname=$(get_hostname $ip)
                [ -z "$hostname" ] && hostname="unknown"
            fi
            
            # Truncate hostname if too long
            if [ ${#hostname} -gt 15 ]; then
                hostname="${hostname:0:15}..."
            fi
            
            # Short mac format
            short_mac=$(echo $mac | cut -d':' -f4-6)
            
            # Print in a more compact format
            printf "%s %s (%s)\n" "$icon" "$ip" "$hostname"
        done < /tmp/dhcp.leases
    fi
}

# Get additional connected devices from ARP table that might not be in DHCP leases
process_arp_table() {
    # Create a temporary file with the IPs from DHCP leases to avoid duplicates
    touch /tmp/user_sh_dhcp_ips
    if [ -f "/tmp/dhcp.leases" ]; then
        awk '{print $3}' /tmp/dhcp.leases > /tmp/user_sh_dhcp_ips
    fi
    
    # Parse ARP table
    ip neigh show | grep -v FAILED | while read -r ip _ _ mac _ _; do
        # Skip IP addresses already listed in DHCP leases
        grep -q "^$ip$" /tmp/user_sh_dhcp_ips && continue
        
        # Get hostname
        hostname=$(get_hostname $ip)
        [ -z "$hostname" ] && hostname="unknown"
        
        # Truncate hostname if too long
        if [ ${#hostname} -gt 15 ]; then
            hostname="${hostname:0:15}..."
        fi
        
        # Get device icon
        icon=$(get_device_icon $mac)
        
        # Short mac format
        short_mac=$(echo $mac | cut -d':' -f4-6)
        
        # Print in a more compact format
        printf "%s %s (%s)\n" "$icon" "$ip" "$hostname"
    done
    
    # Clean up temporary file
    rm -f /tmp/user_sh_dhcp_ips
}

# Count online devices
count_online_devices() {
    local count=0
    if [ -f "/tmp/dhcp.leases" ]; then
        count=$(wc -l < /tmp/dhcp.leases)
    fi
    echo $count
}

# Main function
main() {
    print_header
    
    # Process DHCP leases first
    process_dhcp_leases
    
    # Then add any devices from ARP table that weren't in DHCP leases
    process_arp_table
    
    # Add footer
    echo ""
    echo "✦✦✦✦✦ REVD.CLOUD ✦✦✦✦✦"
}

# Run the main function
main
