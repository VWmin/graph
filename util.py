import heapq
import random

import networkx as nx


class PriorityQueue:
    container = []

    def push(self, item):
        heapq.heappush(self.container, item)

    def pop(self):
        return heapq.heappop(self.container)

    def size(self):
        return len(self.container)


def verify_labels(g: nx.Graph, correct_l, test_l, use_sp=False):
    from pll_weighted import query_distance as d
    for u in g.nodes:
        for v in g.nodes:
            excepted = nx.single_source_dijkstra(g, u, v)[0] if use_sp else d(correct_l, u, v)
            got = d(test_l, u, v)
            if excepted != got:
                print(f"in {u, v}, excepted: {excepted}, got: {got}")


def random_s_with_number(total, number):
    ret = set()
    while len(ret) != number:
        ret.add(random.randint(0, total - 1))
    return list(ret)


def random_s2r_with_number(total, number, S):
    ret = {}
    for s in S:
        ret[s] = set()
        while len(ret[s]) != number:
            t = random.randint(0, total - 1)
            if t == s:
                continue
            ret[s].add(t)
    return ret


def random_d_with_range(S, lo, hi):
    D = {}
    for s in S:
        D[s] = random.randint(lo, hi)
    return D
