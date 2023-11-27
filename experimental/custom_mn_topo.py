from mininet.topo import Topo
import networkx as nx


def gt_itm_example() -> nx.Graph:
    # filename = r"sample-graphs/ts/ts600/ts600-0.alt"
    filename = r"sample-graphs/ts/ts100/ts100-0.alt"
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
    def __init__(self, graph: nx.Graph, host_range):
        self.graph = graph
        self.host_range = host_range
        super().__init__()

    def build(self):
        for n in self.graph.nodes:
            self.addSwitch("s_%s" % n)
            # Add single host on designated switches
            # if int(n) in self.host_range:
            self.addHost("h%s" % n)
            # directly add the link between hosts and their gateways
            self.addLink("s_%s" % n, "h%s" % n)
        # Connect your switches to each other as defined in networkx graph
        for (n1, n2) in self.graph.edges:
            self.addLink('s_%s' % n1, 's_%s' % n2)


# def construct_mininet_from_networkx(graph: nx.Graph, host_range):
#     """ Builds the mininet from a networkx graph.
#
#     :param graph: The networkx graph describing the network
#     :param host_range: All switch indices on which to attach a single host as integers
#     :return: net: the constructed 'Mininet' object
#     """
#
#     net = Mininet()
#     # Construct mininet
#     for n in graph.nodes:
#         net.addSwitch("s_%s" % n)
#         # Add single host on designated switches
#         if int(n) in host_range:
#             net.addHost("h%s" % n)
#             # directly add the link between hosts and their gateways
#             net.addLink("s_%s" % n, "h%s" % n)
#     # Connect your switches to each other as defined in networkx graph
#     for (n1, n2) in graph.edges:
#         net.addLink('s_%s' % n1, 's_%s' % n2)
#     return net


topos = {'mytopo': (lambda: MyTopo(gt_itm_example(), []))}
