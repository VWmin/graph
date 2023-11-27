from mininet.net import Mininet
from mininet.node import OVSController
from mininet.topo import Topo
import networkx as nx


def gt_itm_example() -> nx.Graph:
    filename = r"sample-graphs/ts/ts600/ts600-0.alt"
    # filename = r"sample-graphs/ts/ts100/ts100-0.alt"
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


topos = {'mytopo': lambda: MyTopo(gt_itm_example())}
# net = construct_mininet_from_networkx(gt_itm_example())
# net.start()
# net.pingAll()
# net.stop()

