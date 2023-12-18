import subprocess
import time

import numpy as np
from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import OVSController, RemoteController
from mininet.topo import Topo
import networkx as nx


def gt_itm_example() -> nx.Graph:
    # filename = r"sample-graphs/ts/ts600/ts600-0.alt"
    filename = r"sample-graphs/ts/ts100/ts100-0.alt"
    # filename = r"sample-graphs/rand/r10/r10-0.alt"
    g = nx.Graph()
    with open(filename, "r") as f:
        flag = False
        for line in f.readlines():
            if not flag and line.startswith("EDGES"):
                flag = True
            elif flag:
                arr = line.split(' ')[:2]
                g.add_edge(int(arr[0]), int(arr[1]))
    return g


def as_733_example():
    filename = r"C:\Users\user\Downloads\as-733\as19971109.txt"
    g = nx.Graph()
    with open(filename, "r") as f:
        flag = False
        for line in f.readlines():
            if not flag and line.startswith("# FromNodeId	ToNodeId"):
                flag = True
            elif flag:
                arr = line.split('\t')[:2]
                arr[1] = arr[1][:-1]
                g.add_edge(arr[0], arr[1])


def demo_graph():
    # G = nx.Graph()  # 创建无向图
    # G.add_edge(0, 1, weight=39)
    # G.add_edge(0, 2, weight=33)
    # G.add_edge(0, 3, weight=15)
    # G.add_edge(1, 3, weight=21)
    # G.add_edge(1, 6, weight=46)
    # G.add_edge(2, 4, weight=23)
    # G.add_edge(3, 4, weight=40)
    # G.add_edge(3, 5, weight=18)
    # G.add_edge(3, 6, weight=71)
    # G.add_edge(4, 7, weight=29)
    # G.add_edge(5, 7, weight=25)
    # G.add_edge(5, 8, weight=25)
    # G.add_edge(6, 8, weight=20)
    # G.add_edge(7, 8, weight=45)
    A = np.array([
        [0, 39, 33, 15, 0, 0, 0, 0, 0],
        [39, 0, 0, 21, 0, 0, 46, 0, 0],
        [33, 0, 0, 0, 23, 0, 0, 0, 0],
        [15, 21, 0, 0, 40, 18, 71, 0, 0],
        [0, 0, 23, 40, 0, 0, 0, 29, 0],
        [0, 0, 0, 18, 0, 0, 0, 25, 25],
        [0, 46, 0, 71, 0, 0, 0, 0, 20],
        [0, 0, 0, 0, 29, 25, 0, 0, 45],
        [0, 0, 0, 0, 0, 25, 20, 45, 0],
    ])
    G = nx.from_numpy_array(A)
    return G


class MyTopo(Topo):
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        super().__init__()

    def build(self):
        for n in self.graph.nodes:
            s_name = f"s{n + 1}"
            h_name = f"h{n + 1}"
            self.addSwitch(s_name, dpid=int_to_16bit_hex_string(n + 1))
            # Add single host on designated switches
            self.addHost(h_name)
            # directly add the link between hosts and their gateways
            self.addLink(s_name, h_name)
        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            s_name_1, s_name_2 = f"s{n1 + 1}", f"s{n2 + 1}"
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
    graph = demo_graph()
    custom_topo = MyTopo(graph)
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


# topos = {'mytopo': lambda: MyTopo(demo_graph())}


if __name__ == '__main__':
    run_mn_net()
