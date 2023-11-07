import copy

import random_graph
import pll
import networkx as nx
from math import inf


def inc_pll(G: nx.Graph, L, a, b):
    V = list(L[a].keys() | L[b].keys())
    V.sort()
    d = pll.query_distance
    for v in V:
        if v in L[a]:
            resume_pbfs(G, v, b, d(L, v, a) + 1, L)
        if v in L[b]:
            resume_pbfs(G, v, a, d(L, v, b) + 1, L)
    return L
    # d = pll.query_distance
    # V = L[a].keys() | L[b].keys()
    # for v in G.nodes:
    #     if v in V:
    #         continue
    #     da, db = d(L, v, a), d(L, v, b)
    #     if da <= db:
    #         resume_pbfs(G, v, b, da + 1, L)
    #     else:
    #         resume_pbfs(G, v, a, db + 1, L)
    # return L


def resume_pbfs(G, root, u, d, L):
    que = [(u, d)]
    while que:
        u, d = que.pop(0)
        if d < prefixal_query(L, root, u, root):
            L[u][root] = d
            for v in G.neighbors(u):
                que.append((v, d + 1))


def prefixal_query(labels, u, v, k):
    distance = inf
    common = labels[u].keys() & labels[v].keys()
    for landmark in common:
        if landmark <= k:
            distance = min(distance, labels[u][landmark] + labels[v][landmark])
    return distance


def test_inc_pll():
    G = random_graph.demo_graph()
    # random_graph.print_graph(G, show_weight=False)
    G_raw = copy.deepcopy(G)
    L_raw = pll.process(G)
    print("L raw: ", L_raw)
    # printL(L_raw)
    # printQuery(L_raw, 6, 7)
    G.add_edge(0, 4, weight=20)
    L_new = inc_pll(G, L_raw, 0, 4)
    print("L new: ", L_new)
    # printL(L_new)
    L = pll.process(G)
    print("L    : ", L)
    for u in G.nodes:
        for v in G.nodes:
            excepted = pll.query_distance(L, u, v)
            got = pll.query_distance(L_new, u, v)
            # print(u, v, excepted, got)
            if got != excepted:
                print("disagree in %d-%d, excepted %d, got %d" % (u, v, excepted, got))
    random_graph.print_graph(G)


def printL(L):
    for v in L:
        print("L(%d) = {" % v, end="")
        for u in L[v]:
            print("(%d, %d), " % (u, L[v][u]), end="")
        print("}")


def printQuery(L, a, b):
    V = L[a].keys() & L[b].keys()
    print("d(%d, %d) = min{" % (a, b), end="")
    for v in V:
        print("(%d+%d), " % (L[a][v], L[b][v]), end="")
    print("}")


if __name__ == '__main__':
    test_inc_pll()
