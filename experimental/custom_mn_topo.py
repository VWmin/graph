import numpy as np
from mininet.net import Mininet
from mininet.node import OVSController
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
            s_name = f"s{n}"
            h_name = f"h{n}"
            self.addSwitch(s_name, stp=True, failMode='standalone')
            # Add single host on designated switches
            self.addHost(h_name)
            # directly add the link between hosts and their gateways
            self.addLink(s_name, h_name)
        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            s_name_1, s_name_2 = f"s{n1}", f"s{n2}"
            self.addLink(s_name_1, s_name_2)


# def construct_mininet_from_networkx(graph: nx.Graph):
#     """ Builds the mininet from a networkx graph.
#
#     :param graph: The networkx graph describing the network
#     :return: net: the constructed 'Mininet' object
#     """
#     net = Mininet(controller=OVSController)
#     # Construct mininet
#     for n in graph.nodes:
#         s_name = f"s{n}"
#         h_name = f"h{n}"
#         net.addSwitch(s_name, stp=True, failMode='standalone')
#         # Add single host on designated switches
#         net.addHost(h_name)
#         # directly add the link between hosts and their gateways
#         net.addLink(s_name, h_name)
#     # Connect your switches to each other as defined in networkx graph
#     for (n1, n2) in graph.edges:
#         s_name_1, s_name_2 = f"s{n1}", f"s{n2}"
#         net.addLink(s_name_1, s_name_2)
#     return net


topos = {'mytopo': lambda: MyTopo(demo_graph())}
# net = construct_mininet_from_networkx(gt_itm_example())
# net.start()
# net.pingAll()
# net.stop()
