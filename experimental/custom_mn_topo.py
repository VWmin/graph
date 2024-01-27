import random
import signal
import socket
import subprocess
import sys
import threading
import time

from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo

from mininet.util import customClass
from mininet.link import TCLink

import experiment_ev


def int_to_16bit_hex_string(number: int):
    # 使用 hex 函数转换为十六进制字符串（带前缀 "0x"）
    hex_string_with_prefix = hex(number)
    # 去除前缀，并使用 upper 方法将字母转为大写
    hex_string_without_prefix = hex_string_with_prefix[2:].upper()
    hex_string_fixed_length = hex_string_without_prefix.zfill(16)
    return hex_string_fixed_length


def int_to_ip_address(number: int):
    third_octet = (number - 1) // 254
    fourth_octet = (number - 1) % 254 + 1
    return f"10.0.{third_octet}.{fourth_octet}"


class MyTopo(Topo):
    def __init__(self, info):
        self.info = info
        self.graph = info.graph
        super().__init__()

    def build(self):
        # related host
        terminals = set()
        for s in self.info.S2R:
            terminals.add(s)
            for r in self.info.S2R[s]:
                terminals.add(r)

        for n in self.graph.nodes:
            s_name = f"s{n}"
            h_name = f"h{n}"
            if self.info.stp:
                self.addSwitch(s_name, dpid=int_to_16bit_hex_string(n), stp=True, failMode='standalone')
            else:
                self.addSwitch(s_name, dpid=int_to_16bit_hex_string(n))
            if n in terminals:
                # Add single host on designated switches
                self.addHost(h_name, ip=int_to_ip_address(n))
                # directly add the link between hosts and their gateways
                self.addLink(s_name, h_name)

        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            s_name_1, s_name_2 = f"s{n1}", f"s{n2}"
            self.addLink(s_name_1, s_name_2, cls=TCLink,
                         bw=self.graph[n1][n2]['bandwidth'], delay=f"{self.graph[n1][n2]['weight']}ms")


class MininetEnv:
    # Rate limit links to 10Mbps
    link = customClass({'tc': TCLink}, 'tc,bw=10')

    def __init__(self):
        self.finished = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.info = experiment_ev.acquire_info()
        custom_topo = MyTopo(self.info)
        controller = RemoteController('c0')
        # self.net = Mininet(topo=custom_topo, controller=controller, link=MininetEnv.link)
        self.net = Mininet(topo=custom_topo, controller=controller)

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("Received signal to exit.")
        self.server.close()
        if self.net is not None:
            self.net.stop()
        sys.exit(0)

    def start(self):
        self.net.start()

        threads = [threading.Thread(target=self.run_mn_cli), threading.Thread(target=self.run_mn_cmd_server)]
        if self.info.stp:
            threads.append(threading.Thread(target=self.ping_connectivity))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.net.stop()

    @staticmethod
    def run_command_async(host, command):
        # 异步运行命令
        return host.popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def run_mn_cli(self):
        CLI(self.net)
        self.finished = True

    def ping_connectivity(self):
        hosts_to_ping = random.sample(self.info.S2R[random.choice(list(self.info.S))], 2)
        ha, hb = self.net.get(f'h{hosts_to_ping[0]}'), self.net.get(f"h{hosts_to_ping[1]}")
        t1 = time.time()
        connected, turn = False, 1
        while not connected:
            result = ha.cmd('ping -c 1', hb.IP())
            print(f"turn {turn}, result: {result}")
            if "1 packets transmitted, 1 received" in result:
                connected = True
        t2 = time.time()
        print(f"cost: {t2 - t1}")

    def run_mn_cmd_server(self):
        self.server.bind(('127.0.0.1', 8889))
        self.server.listen(1)

        connection, address = self.server.accept()
        raw_msg = connection.recv(1024)
        msg = raw_msg.decode()
        if msg and msg == "ok":
            self.run_script()
            time.sleep(15)
            self.run_iperf()
        connection.close()

        self.server.close()

    def run_script(self):
        print("\nstarting script")
        for s in self.info.S2R:
            for r in self.info.S2R[s]:
                self.run_script_on_host(f"h{r}", f"./recv -g {self.info.src_to_group_no[s]}")
            self.run_script_on_host(f"h{s}", f"./send -i {self.info.src_to_group_ip(s)}")

    def run_iperf(self):
        print("\nstarting iperf")
        for s in self.info.S2R:
            multicast_ip = self.info.src_to_group_ip(s)
            for r in self.info.S2R[s]:
                self.run_script_on_host(f"h{r}", f"./run_iperf_server.sh {multicast_ip} h{r}")
            self.run_script_on_host(f"h{s}", f"./run_iperf_client.sh {multicast_ip} h{s} {self.info.B[s]}M")

    def run_script_on_host(self, hostname, cmd):
        host = self.net.getNodeByName(hostname)
        self.run_command_async(host, cmd)
        print(f"{hostname} {cmd}")


if __name__ == '__main__':
    setLogLevel('info')
    ev = MininetEnv()
    ev.start()
