import signal
import socket
import subprocess
import sys
import threading

from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo
import networkx as nx

import experiment_ev
from experiment_info import ExperimentInfo


def int_to_16bit_hex_string(number: int):
    # 使用 hex 函数转换为十六进制字符串（带前缀 "0x"）
    hex_string_with_prefix = hex(number)
    # 去除前缀，并使用 upper 方法将字母转为大写
    hex_string_without_prefix = hex_string_with_prefix[2:].upper()
    hex_string_fixed_length = hex_string_without_prefix.zfill(16)
    return hex_string_fixed_length


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
            self.addSwitch(s_name, dpid=int_to_16bit_hex_string(n))
            if n in terminals:
                # Add single host on designated switches
                self.addHost(h_name)
                # directly add the link between hosts and their gateways
                self.addLink(s_name, h_name)
        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            s_name_1, s_name_2 = f"s{n1}", f"s{n2}"
            self.addLink(s_name_1, s_name_2)


class MininetEnv:
    def __init__(self):
        self.finished = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.info = experiment_ev.acquire_info()
        custom_topo = MyTopo(self.info)
        controller = RemoteController('c0')
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

        cli_thread = threading.Thread(target=self.run_mn_cli)
        cmd_thread = threading.Thread(target=self.run_mn_cmd_server)

        cli_thread.start()
        cmd_thread.start()

        cli_thread.join()
        cmd_thread.join()

        self.net.stop()

    @staticmethod
    def run_command_async(host, command):
        # 异步运行命令
        return host.popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def run_mn_cli(self):
        CLI(self.net)
        self.finished = True

    def run_mn_cmd_server(self):
        self.server.bind(('127.0.0.1', 8889))
        self.server.listen(1)

        connection, address = self.server.accept()
        raw_msg = connection.recv(1024)
        msg = raw_msg.decode()
        if msg and msg == "ok":
            self.run_script()
        connection.close()

        self.server.close()

    def run_script(self):
        print("\nstarting script")
        for s in self.info.S2R:
            for r in self.info.S2R[s]:
                self.run_script_on_host(f"h{r}", "./recv")
            self.run_script_on_host(f"h{s}", "./send")

    def run_script_on_host(self, hostname, cmd):
        host = self.net.getNodeByName(hostname)
        self.run_command_async(host, cmd)
        print(f"{hostname} {cmd}")


if __name__ == '__main__':
    setLogLevel('info')
    ev = MininetEnv()
    ev.start()
