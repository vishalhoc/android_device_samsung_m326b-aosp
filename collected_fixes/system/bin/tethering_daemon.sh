#!/system/bin/sh

# Set global tethering properties
settings put global tether_dun_required 0
settings put global tether_offload_disabled 1

(
while true; do
    if ip link show rndis0 2>/dev/null | grep -q "UP" || ip link show swlan0 2>/dev/null | grep -q "UP"; then
        echo 1 > /proc/sys/net/ipv4/ip_forward
        echo 1 > /proc/sys/net/ipv6/conf/all/forwarding

        # Policy routing rules
        ip rule add from all iif rndis0 lookup v4-rmnet0 prio 15000 2>/dev/null
        ip rule add from all iif rndis0 lookup rmnet0 prio 15001 2>/dev/null
        ip rule add from all iif swlan0 lookup v4-rmnet0 prio 15002 2>/dev/null
        ip rule add from all iif swlan0 lookup rmnet0 prio 15003 2>/dev/null

        # NAT MASQUERADE
        iptables -t nat -C POSTROUTING -o v4-rmnet0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o v4-rmnet0 -j MASQUERADE
        iptables -t nat -C POSTROUTING -o rmnet0 -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o rmnet0 -j MASQUERADE

        # DNS Redirect to 8.8.8.8
        iptables -t nat -C PREROUTING -i rndis0 -p udp --dport 53 -j DNAT --to-destination 8.8.8.8:53 2>/dev/null || iptables -t nat -I PREROUTING 1 -i rndis0 -p udp --dport 53 -j DNAT --to-destination 8.8.8.8:53
        iptables -t nat -C PREROUTING -i rndis0 -p tcp --dport 53 -j DNAT --to-destination 8.8.8.8:53 2>/dev/null || iptables -t nat -I PREROUTING 2 -i rndis0 -p tcp --dport 53 -j DNAT --to-destination 8.8.8.8:53
        iptables -t nat -C PREROUTING -i swlan0 -p udp --dport 53 -j DNAT --to-destination 8.8.8.8:53 2>/dev/null || iptables -t nat -I PREROUTING 3 -i swlan0 -p udp --dport 53 -j DNAT --to-destination 8.8.8.8:53
        iptables -t nat -C PREROUTING -i swlan0 -p tcp --dport 53 -j DNAT --to-destination 8.8.8.8:53 2>/dev/null || iptables -t nat -I PREROUTING 4 -i swlan0 -p tcp --dport 53 -j DNAT --to-destination 8.8.8.8:53

        # Forward rules
        iptables -C FORWARD -i rndis0 -o v4-rmnet0 -j ACCEPT 2>/dev/null || iptables -I FORWARD 1 -i rndis0 -o v4-rmnet0 -j ACCEPT
        iptables -C FORWARD -i swlan0 -o v4-rmnet0 -j ACCEPT 2>/dev/null || iptables -I FORWARD 2 -i swlan0 -o v4-rmnet0 -j ACCEPT
        iptables -C FORWARD -i rndis0 -o rmnet0 -j ACCEPT 2>/dev/null || iptables -I FORWARD 3 -i rndis0 -o rmnet0 -j ACCEPT
        iptables -C FORWARD -i swlan0 -o rmnet0 -j ACCEPT 2>/dev/null || iptables -I FORWARD 4 -i swlan0 -o rmnet0 -j ACCEPT
    fi
    sleep 3
done
) &
