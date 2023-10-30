import copy
import random_graph
import pll_weighted
import networkx as nx
from math import inf
import heapq


class PriorityQueue:
    container = []

    def push(self, item):
        heapq.heappush(self.container, item)

    def pop(self):
        return heapq.heappop(self.container)

    def size(self):
        return len(self.container)


def affected(Gi: nx.Graph, Gi_1: nx.Graph, L, x, y):
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
                    if (h in A) or ((h == u or h == y) and (d(L, u, y) == d(L, u, x) + Gi_1[x][y]['weight'])):
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
    if len(AX) < len(AY):
        LA, SA = AX, AY
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


def test_remove_edge():
    G = random_graph.demo_graph()
    L = pll_weighted.weighted_pll(G)
    print("origin L: ", L)
    G_old = copy.deepcopy(G)
    G.remove_edge(2, 4)
    AX, AY = affected(G, G_old, L, 2, 4), affected(G, G_old, L, 4, 2)
    # AX, AY = alternative_affected(G, G_old, L, 2, 4), alternative_affected(G, G_old, L, 4, 2)
    print("affected X: ", AX)
    print("affected Y: ", AY)
    L2 = remove_affected_labels(L, AX, AY)
    print("remove L: ", L2)
    L3 = order_restore(G, L2, AX, AY)
    # L3 = greedy_restore(G, L2, AX, AY)
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
    Gi_1 = random_graph.random_graph(100, .2, 100)
    Gi = copy.deepcopy(Gi_1)


if __name__ == '__main__':
    test_remove_edge()
    #
    # q = []
    #
    # heapq.heappush(q, (2, 'code'))
    # heapq.heappush(q, (1, 'eat'))
    # heapq.heappush(q, (3, 'sleep'))
    #
    # while q:
    #     next_item = heapq.heappop(q)
    #     print(next_item)
