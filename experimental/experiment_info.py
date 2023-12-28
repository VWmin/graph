import networkx as nx


class ExperimentInfo:
    def __init__(self, graph: nx.Graph):
        self.graph = nx.Graph()
        # renumbered to 1-n
        for edge in graph.edges:
            self.graph.add_edge(edge[0] + 1, edge[1] + 1)

        b_lo, b_hi = 5e6 / 2, 10e6 / 2  # use half of the bandwidth for multicast
        b_req_lo, b_req_hi = 512 * 1e3, 1e6  # per multicast required
        d_lo, d_hi = 1, 10
        d_req_lo, d_req_hi = 50, 100

        import util

        util.add_attr_with_random_value(self.graph, "bandwidth", int(b_lo), int(b_hi))
        util.add_attr_with_random_value(self.graph, "weight", d_lo, d_hi)
        self.S = util.random_s_from_graph(self.graph, 5)
        self.S2R = util.random_s2r_from_graph(self.graph, 5, self.S)
        self.B = util.random_d_with_range(self.S, int(b_req_lo), int(b_req_hi))
        self.D = util.random_d_with_range(self.S, d_req_lo, d_req_hi)

        group_no = 1
        self.src_to_group_no = {}
        for s in self.S2R:
            self.src_to_group_no[s] = group_no
            group_no += 1

    def src_to_group_ip(self, src):
        return f'224.0.1.{self.src_to_group_no[src]}'

