import copy

import random_graph
import pll
import networkx as nx
from math import inf


def affected(G: nx.Graph, G_old, L, x, y):
    d = nx.shortest_path_length
    A = set()
    mark = {}
    for v in G.nodes:
        mark[v] = False
    que = []
    mark[x] = True
    que.append(x)
    while len(que):
        v = que[0]
        que.pop(0)
        A.add(v)
        for u in G.neighbors(v):
            if not mark[u]:
                H = pll.find_hub(L, u, y)
                for h in H:
                    if (h in A) or ((h == u or h == y) and (d(G_old, u, y) == d(G_old, u, x) + 1)):
                        mark[u] = True
                        que.append(u)
                        break
    return A


def alternative_affected(G: nx.Graph, L, x, y):
    A = set()
    mark = {}
    for v in G.nodes:
        mark[v] = False
    que = []
    mark[x] = True
    que.append(x)
    while len(que):
        v = que[0]
        que.pop(0)
        A.add(v)
        for u in G.neighbors(v):
            if not mark[u]:
                d = nx.shortest_path_length
                if d(G, u, y) != pll.query_distance(L, u, y):
                    mark[u] = True
                    que.append(u)
                else:
                    h = min(list(pll.find_hub(L, u, y)))
                    if h in A or ((h == u or h == y) and d(G, u, y) == d(G, u, x) + 1):
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
    query = pll.query_distance
    SA, LA = AX, AY
    if len(AX) < len(AY):
        LA, SA = AX, AY
    for a in SA:
        mark, dist = {}, {}
        for v in G.nodes:
            mark[v], dist[v] = False, inf
        que = []
        mark[a], dist[a] = True, 0
        while len(que):
            v = que[0]
            que.pop(0)
            if v in LA:
                if dist[v] < query(L, a, v):
                    if v < a:
                        L[a][v] = dist[v]
                    else:
                        L[v][a] = dist[v]
            for u in G.neighbors(v):
                if not mark[u]:
                    dist[u], mark[u] = dist[v]+1, True
                    que.append(u)
    return L


def order_restore(G: nx.Graph, L, AX, AY):
    from pll import query_distance as d
    F = list(AX | AY)
    F.sort()
    for a in F:
        mark = {}
        dist = {}
        for v in G.nodes:
            mark[v] = False
            dist[v] = inf
        que = []
        mark[a] = True
        dist[a] = 0
        que.append(a)
        while len(que):
            v = que[0]
            que.pop(0)
            if v < a:
                continue
            if (a in AX and v in AY) or (a in AY and v in AX):
                if dist[v] < d(L, a, v):
                    L[v][a] = dist[v]
            for u in G.neighbors(v):
                if not mark[u]:
                    dist[u] = dist[v] + 1
                    mark[u] = True
                    que.append(u)
    return L


def test_remove_edge():
    G = random_graph.demo_graph()
    L = pll.pruned_landmark_labeling(G)
    print("origin L: ", L)
    G_old = copy.deepcopy(G)
    G.remove_edge(2, 4)
    AX = affected(G, G_old, L, 2, 4)
    AY = affected(G, G_old, L, 4, 2)
    print("affected X: ", AX)
    print("affected Y: ", AY)
    L2 = remove_affected_labels(L, AX, AY)
    print("remove L: ", L2)
    L3 = order_restore(G, L2, AX, AY)
    print("restoreL: ", L3)
    L_new = pll.pruned_landmark_labeling(G)
    print("final  L: ", L_new)

    from pll import query_distance as d
    for u in G.nodes:
        for v in G.nodes:
            if d(L3, u, v) != d(L_new, u, v):
                print(u, v, d(L3, u, v), d(L_new, u, v))
    random_graph.print_graph(G, False)


if __name__ == '__main__':
    test_remove_edge()
    # https://link.springer.com/article/10.1007/s00778-021-00707-z
