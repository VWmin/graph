import subprocess

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.topo import Topo
import networkx as nx

import experiment_ev
from experiment_info import ExperimentInfo


class MyTopo(Topo):
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        super().__init__()

    def build(self):
        for n in self.graph.nodes:
            s_name = f"s{n}"
            h_name = f"h{n}"
            self.addSwitch(s_name, dpid=int_to_16bit_hex_string(n))
            # Add single host on designated switches
            self.addHost(h_name)
            # directly add the link between hosts and their gateways
            self.addLink(s_name, h_name)
        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            s_name_1, s_name_2 = f"s{n1}", f"s{n2}"
            self.addLink(s_name_1, s_name_2)


def int_to_16bit_hex_string(number: int):
    # 使用 hex 函数转换为十六进制字符串（带前缀 "0x"）
    hex_string_with_prefix = hex(number)
    # 去除前缀，并使用 upper 方法将字母转为大写
    hex_string_without_prefix = hex_string_with_prefix[2:].upper()
    hex_string_fixed_length = hex_string_without_prefix.zfill(16)
    return hex_string_fixed_length


def run_command_async(host, command):
    # 异步运行命令
    return host.popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_mn_net():
    info: ExperimentInfo = experiment_ev.acquire_info()
    custom_topo = MyTopo(info.graph)
    controller = RemoteController('c0')
    net = Mininet(topo=custom_topo, controller=controller)
    net.start()

    # host1, host2 = net.getNodeByName('h1'), net.getNodeByName('h2')
    # t1 = time.time()

    # 异步运行命令
    # process_host1 = run_command_async(host1, './send')
    # process_host2 = run_command_async(host2, './send')

    # # block until finished
    # output_host1, error_host1 = process_host1.communicate()
    # output_host2, error_host2 = process_host2.communicate()
    #
    # # 打印输出和错误
    # print(f"Command output on h1: {output_host1}")
    # print(f"Command error on h1: {error_host1}")
    # print(f"Command output on h2: {output_host2}")
    # print(f"Command error on h2: {error_host2}")
    # print(time.time() - t1)

    CLI(net)
    net.stop()


if __name__ == '__main__':
    run_mn_net()
