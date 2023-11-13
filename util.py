import heapq

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
