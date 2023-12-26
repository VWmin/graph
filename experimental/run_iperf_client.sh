#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <listen_address> <hostname>"
    exit 1
fi

multicast_ip="$1"
hostname="$2"

ip route add 224.0.0.0/4 dev "${hostname}"-eth0
iperf -c "${multicast_ip}" -u -T 32 -t 10 -i 1