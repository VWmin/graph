import json
import math
import random

import networkx as nx



class ExperimentInfo:
    def __init__(self, graph: nx.Graph):
        self.graph = nx.Graph()
        # renumbered to 1-n
        for edge in graph.edges:
            self.graph.add_edge(edge[0] + 1, edge[1] + 1)

        b_lo, b_hi = 5, 10
        b_req_lo, b_req_hi = 1, 2
        d_lo, d_hi = 1, 10
        d_req_lo, d_req_hi = 50, 100

        random.seed(42)

        self.total_bw = set_random_bw(self.graph, "bandwidth", b_lo, b_hi)
        add_attr_with_random_value(self.graph, "weight", d_lo, d_hi)
        self.S = random_s_from_graph(self.graph, 1)
        self.S2R = random_s2r_from_graph(self.graph, 10, self.S)
        self.B = random_b_with_range(self.S, b_req_lo, b_req_hi)
        self.D = random_d_with_range(self.S, d_req_lo, d_req_hi)

        self.stp = False

        print(f"src set is {self.S}")
        print(f"src to recv is {self.S2R}")
        print(f"total bw is {self.total_bw}")
        print(f"bw requirement is {self.B}")

        group_no = 1
        self.src_to_group_no = {}
        for s in self.S2R:
            self.src_to_group_no[s] = group_no
            group_no += 1

        output = {
            "s2r": {},
            "bw_requirement": self.B,
            "total_bw": self.total_bw,
            "src_to_group": self.src_to_group_no
        }
        for s in self.S2R:
            output["s2r"][s] = []
            for r in self.S2R[s]:
                output["s2r"][s].append(r)

        with open('ev_setting.json', 'w') as json_file:
            json.dump(output, json_file, indent=4)

    def src_to_group_ip(self, src):
        return f'224.0.1.{self.src_to_group_no[src]}'

    def add_random_r(self):
        s = random.choice(list(self.S))
        nodes = list(self.graph.nodes)
        r = random.choice(nodes)
        while r in self.S2R[s]:
            r = random.choice(nodes)
        self.S2R[s].add(r)
        print(f"add receiver {r}")

    def remove_random_r(self):
        s = random.choice(list(self.S))
        r = random.choice(list(self.S2R[s]))
        self.S2R[s].remove(r)
        print(f"remove receiver {r}")

    def inc_link_delay(self, u, v):
        self.graph[u][v]['weight'] = self.graph[u][v]['weight'] * 1.3
        print(f"inc edge {u, v} delay")

    def disable_link(self, u, v):
        self.graph[u][v]['weight'] = math.inf
        print(f"disable edge {u, v}")


def add_attr_with_random_value(g, name, lo, hi):
    for u, v in g.edges:
        g[u][v][name] = random.randint(lo, hi)


def set_random_bw(g, name, lo, hi):
    tot = 0
    for u, v in g.edges:
        bw = random.randint(lo, hi)
        tot += bw
        g[u][v][name] = bw
    return tot


def random_b_with_range(S, lo, hi):
    B = {}
    for s in S:
        B[s] = round(random.uniform(lo, hi), 1)
    return B


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


# if __name__ == '__main__':
# import random_graph

#     expinfo = ExperimentInfo(graph=random_graph.gt_itm_ts(100))
#     print(expinfo.S2R)
#     expinfo.add_random_r()
#     print(expinfo.S2R)
#     expinfo.remove_random_r()
#     print(expinfo.S2R)
