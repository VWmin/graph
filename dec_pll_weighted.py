import copy
import random

import random_graph
import pll_weighted
import networkx as nx
from math import inf
from util import PriorityQueue


def affected(Gi: nx.Graph, raw_w, L, x, y):
    # d = nx.dijkstra_path_length
    d = pll_weighted.query_distance
    A, mark = set(), {}
    for v in Gi.nodes:
        mark[v] = False
    que, mark[x] = [x], True
    while len(que):
        v = que[0]
        que.pop(0)
        A.add(v)
        for u in Gi.neighbors(v):
            if not mark[u]:
                H = pll_weighted.find_hub(L, u, y)
                for h in H:
                    if (h in A) or ((h == u or h == y) and (d(L, u, y) == d(L, u, x) + raw_w)):
                        mark[u] = True
                        que.append(u)
                        break
    return A


def alternative_affected(Gi: nx.Graph, Gi_1: nx.Graph, L, x, y):
    d = nx.dijkstra_path_length
    A, mark = set(), {}
    for v in Gi.nodes:
        mark[v] = False
    que, mark[x] = [x], True
    while len(que):
        v = que[0]
        que.pop(0)
        A.add(v)
        for u in Gi.neighbors(v):
            if not mark[u]:
                if d(Gi, u, y) != d(Gi_1, u, y):
                    mark[u] = True
                    que.append(u)
                else:
                    h = min(list(pll_weighted.find_hub(L, u, y)))
                    if h in A or ((h == u or h == y) and d(Gi_1, u, y) == d(Gi_1, u, x) + Gi_1[x][y]['weight']):
                        mark[u] = True
                        que.append(u)
    return A


def remove_affected_labels(L, AX, AY):
    for v in AX:
        for u in AY:
            if u in L[v].keys():
                del L[v][u]
    for v in AY:
        for u in AX:
            if u in L[v].keys():
                del L[v][u]
    return L


def greedy_restore(G: nx.Graph, L, AX, AY):
    query = pll_weighted.query_distance
    SA, LA = AX, AY
    if len(AY) < len(AX):
        SA, LA = AY, AX
    for a in SA:
        mark, dist = {}, {}
        for v in G.nodes:
            mark[v], dist[v] = False, inf
        que = PriorityQueue()
        que.push((0, a))
        mark[a], dist[a] = True, 0
        while que.size():
            _, v = que.pop()
            if mark[v]:
                continue
            mark[v] = True
            if v in LA:
                if dist[v] < query(L, a, v):
                    if v < a:
                        L[a][v] = dist[v]
                    else:
                        L[v][a] = dist[v]
            for u in G.neighbors(v):
                if dist[u] > dist[v] + G[u][v]['weight']:
                    dist[u] = dist[v] + G[u][v]['weight']
                    que.push((dist[u], u))
    return L


def order_restore(G: nx.Graph, L, AX, AY):
    from pll_weighted import query_distance as d
    F = list(AX | AY)
    F.sort()
    for a in F:
        mark, dist = {}, {}
        for v in G.nodes:
            mark[v], dist[v] = False, inf
        que = PriorityQueue()
        que.push((0, a))
        mark[a], dist[a] = True, 0
        while que.size():
            _, v = que.pop()
            if v < a or mark[v]:
                continue
            mark[v] = True
            if (a in AX and v in AY) or (a in AY and v in AX):
                if dist[v] < d(L, a, v):
                    L[v][a] = dist[v]
            for u in G.neighbors(v):
                if dist[u] > dist[v] + G[u][v]['weight']:
                    dist[u] = dist[v] + G[u][v]['weight']
                    que.push((dist[u], u))
    return L


def dec_pll_w(g: nx.Graph, raw_w, x, y, l0):
    AX, AY = affected(g, raw_w, l0, x, y), affected(g, raw_w, l0, y, x)
    l1_no_affected = remove_affected_labels(l0, AX, AY)
    # l1 = order_restore(g, l1_no_affected, AX, AY)
    l1 = greedy_restore(g, l1_no_affected, AX, AY)
    return l1


def test_remove_edge():
    G = random_graph.demo_graph()
    L = pll_weighted.weighted_pll(G)
    print("origin L: ", L)
    G_old = copy.deepcopy(G)
    u, v = 3, 6
    raw_w = G[u][v]['weight']
    G.remove_edge(u, v)
    AX, AY = affected(G, raw_w, L, u, v), affected(G, raw_w, L, v, u)
    # AX, AY = alternative_affected(G, G_old, L, 2, 4), alternative_affected(G, G_old, L, 4, 2)
    print("affected X: ", AX)
    print("affected Y: ", AY)
    L2 = remove_affected_labels(L, AX, AY)
    print("remove L: ", L2)
    # L3 = order_restore(G, L2, AX, AY)
    L3 = greedy_restore(G, L2, AX, AY)
    print("restoreL: ", L3)
    L_new = pll_weighted.weighted_pll(G)
    print("final  L: ", L_new)

    from pll_weighted import query_distance as d
    for u in G.nodes:
        for v in G.nodes:
            if d(L3, u, v) != d(L_new, u, v):
                print(u, v, d(L3, u, v), d(L_new, u, v))
    random_graph.print_graph(G)
    random_graph.print_graph(G_old)


def test_remove_random_edge():
    g0 = random_graph.demo_graph()
    g1 = copy.deepcopy(g0)
    l0 = pll_weighted.weighted_pll(g0)
    print(l0)

    # remove random edge
    edges = list(g1.edges)
    # u, v = edges[random.randint(0, len(edges) - 1)]
    u, v = 3, 6
    raw_w = g1[u][v]['weight']
    g1.remove_edge(u, v)
    print(f"removed edge {u, v} with w={raw_w}.")

    l1_from_scratch = pll_weighted.weighted_pll(g1)
    l1_dec_pll = dec_pll_w(g1, raw_w, u, v, l0)
    from util import verify_labels
    print(l1_from_scratch)
    print(l1_dec_pll)
    verify_labels(g1, l1_from_scratch, l1_dec_pll, use_sp=True)


if __name__ == '__main__':
    test_remove_edge()
    # test_remove_random_edge()