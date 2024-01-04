import random

import networkx as nx


class ExperimentInfo:
    def __init__(self, graph: nx.Graph):
        self.graph = nx.Graph()
        # renumbered to 1-n
        for edge in graph.edges:
            self.graph.add_edge(edge[0] + 1, edge[1] + 1)

        b_lo, b_hi = 5, 10
        b_req_lo, b_req_hi = 0.5, 1
        d_lo, d_hi = 1, 2
        d_req_lo, d_req_hi = 50, 100

        random.seed(42)

        add_attr_with_random_value(self.graph, "bandwidth", b_lo, b_hi)
        add_attr_with_random_value(self.graph, "weight", d_lo, d_hi)
        self.S = random_s_from_graph(self.graph, 5)
        self.S2R = random_s2r_from_graph(self.graph, 5, self.S)
        self.B = random_d_with_range(self.S, b_req_lo, b_req_hi)
        self.D = random_d_with_range(self.S, d_req_lo, d_req_hi)

        print(f"src to recv is {self.S2R}")

        group_no = 1
        self.src_to_group_no = {}
        for s in self.S2R:
            self.src_to_group_no[s] = group_no
            group_no += 1

    def src_to_group_ip(self, src):
        return f'224.0.1.{self.src_to_group_no[src]}'


def add_attr_with_random_value(g, name, lo, hi):
    for u, v in g.edges:
        g[u][v][name] = random.randint(lo, hi)


def random_d_with_range(S, lo, hi):
    D = {}
    for s in S:
        D[s] = random.uniform(lo, hi)
    return D


def random_s_from_graph(g: nx.Graph, number):
    ret = set()
    nodes = list(g.nodes)
    while len(ret) != number:
        t = random.choice(nodes)
        ret.add(t)
    return ret


def random_s2r_from_graph(g: nx.Graph, number, src_set):
    ret = {}
    used = set()
    nodes = list(g.nodes)
    for s in src_set:
        ret[s] = set()
        used.add(s)
        while len(ret[s]) != number:
            t = random.choice(nodes)
            if t in used:
                continue
            ret[s].add(t)
            used.add(t)
    return ret
