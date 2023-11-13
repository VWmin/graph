import random
import networkx as nx
import pll_weighted
import random_graph
from util import PriorityQueue
from math import inf


def inc_pll_w(g: nx.Graph, l0, a, b):
    to_resume = list(l0[a].keys() | l0[b].keys())
    to_resume.sort()
    d = pll_weighted.query_distance
    for v in to_resume:
        if v in l0[a]:
            resume_pbfs(g, v, b, d(l0, v, a) + g[a][b]['weight'], l0)
        if v in l0[b]:
            resume_pbfs(g, v, a, d(l0, v, b) + g[a][b]['weight'], l0)
    return l0


def resume_pbfs(g: nx.Graph, root, u, d, l0):
    que = PriorityQueue()
    que.push((d, u))
    while que.size() != 0:
        d, u = que.pop()
        if d < prefixal_query(l0, root, u, root):
            l0[u][root] = d
            for v in g.neighbors(u):
                que.push((d + g[u][v]['weight'], v))


def prefixal_query(labels, u, v, k):
    distance = inf
    common = labels[u].keys() & labels[v].keys()
    for landmark in common:
        if landmark <= k:
            distance = min(distance, labels[u][landmark] + labels[v][landmark])
    return distance


def verify(g, correct_l, test_l):
    from pll_weighted import query_distance as d
    for u in g.nodes:
        for v in g.nodes:
            excepted = d(correct_l, u, v)
            got = d(test_l, u, v)
            # sp = nx.single_source_dijkstra(g1, u, v)
            if excepted != got:
                print(f"in {u, v}, excepted: {excepted}, got: {got}")


def test_inc_pll_w_add_edge():
    g0, g1 = random_graph.demo_graph(), random_graph.demo_graph()
    l0 = pll_weighted.weighted_pll(g0)
    print(l0)

    # add edge
    n = g1.number_of_nodes()
    u, v = random.randint(0, n-1), random.randint(0, n-1)
    while u == v or g0.has_edge(u, v):
        u, v = random.randint(0, n - 1), random.randint(0, n - 1)
    t = random.randint(1, 2)
    g1.add_edge(u, v, weight=t)
    print(f"add new edge {u, v} with weight {t}.")

    l1_from_scratch = pll_weighted.weighted_pll(g1)
    l1_inc_pll = inc_pll_w(g1, l0, u, v)

    # print(l1_from_scratch)
    # print(l1_inc_pll)
    verify(g1, l1_from_scratch, l1_inc_pll)


def test_inc_pll_w_dec_w():
    g0, g1 = random_graph.demo_graph(), random_graph.demo_graph()
    l0 = pll_weighted.weighted_pll(g0)
    print(l0)

    # dec random edge weight
    edges = list(g1.edges)
    u, v = edges[random.randint(0, len(edges) - 1)]
    raw_weight = g1[u][v]['weight']
    g1[u][v]['weight'] = 1
    print(f"dec edge {u, v} from {raw_weight} to {g1[u][v]['weight']}.")

    l1_from_scratch = pll_weighted.weighted_pll(g1)
    l1_inc_pll = inc_pll_w(g1, l0, u, v)

    print(l1_from_scratch)
    print(l1_inc_pll)
    verify(g1, l1_from_scratch, l1_inc_pll)


if __name__ == '__main__':
    # test_inc_pll_w_add_edge()
    test_inc_pll_w_dec_w()
