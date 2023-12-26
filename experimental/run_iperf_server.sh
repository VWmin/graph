#!/bin/bash

# 检查是否提供了监听地址参数
if [ -z "$1" ]; then
    echo "Usage: $0 <listen_address>"
    exit 1
fi

multicast_ip="$1"
outfile="${multicast_ip}-$(ifconfig -a | grep -m 1 -o '^[^ ]*' | tr -d :)"


# 启动iperf服务器，指定监听地址
iperf -s -u -B "$multicast_ip" -i 1 > "$outfile" 2>&1 &

# 等待一段时间（例如60秒）
sleep 30

# 结束iperf服务器进程
pkill iperf
