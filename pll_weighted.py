import networkx as nx
import random_graph
import time
import line_profiler as lp
from queue import PriorityQueue as PQ

inf = 1000000000


def  weighted_pll(G:nx.Graph):
    G = nx.convert_node_labels_to_integers(G, ordering="decreasing degree")
    L = {v:dict() for v in G.nodes}
    for v in G.nodes:
        pruned_dijkstra(G, v, L)
    return L

def pruned_dijkstra(G:nx.Graph, vk, L):
    visited = {v:False for v in G.nodes}
    D = {v:inf for v in G.nodes}
    D[vk] = 0
    pq = PQ()
    pq.put((D[vk], vk))
    while not pq.empty():
        _, u = pq.get()
        if visited[u]:
            continue
        visited[u] = True
        if query_distance(L, vk, u) <= D[u]:
            continue
        L[u][vk] = D[u]
        for w in G.neighbors(u):
            if D[w] > D[u] + G[u][w]["weight"]:
                D[w] = D[u] + G[u][w]["weight"]
                pq.put((D[w], w))


def dijkstra(G:nx.Graph, s):
    visited = [False for _ in range(len(G.nodes))]
    d = [inf for _ in range(len(G.nodes))]
    d[s] = 0
    pq = PQ()
    pq.put((d[s], s))
    while not pq.empty():
        _, u = pq.get()
        if visited[u]:
            continue
        visited[u] = True
        for v in G.neighbors(u):
            duv = G[u][v]["weight"]
            if d[v] > d[u] + duv:
                d[v] = d[u] + duv
                pq.put((d[v], v))
    return d

def query_distance(labels, u, v):
    if u not in labels or v not in labels:
        return inf
    distance = inf
    k = labels[u].keys() & labels[v].keys()
    for landmark in k:
        distance = min(distance, labels[u][landmark] + labels[v][landmark])
    return distance


def test_correctness():
    G = random_graph.random_graph(1000, 0.1, 100)
    # G = random_graph.demo_graph()
    t1 = time.time()
    lables = weighted_pll(G)
    t2 = time.time()
    print("weighted pll: ", t2 - t1)

    d1 = query_distance(lables, 0, 7)
    t3 = time.time()
    print("d1: ", d1)
    print("cost1: ", t3 - t2)

    d2, path = nx.single_source_dijkstra(G, 0, 7)
    t4 = time.time()
    print("d2: ", d2)
    print("cost2: ", t4 - t3)

    d = nx.floyd_warshall(G)
    t5 = time.time()
    print("cost3: ", t5-t4)

    for v in G.nodes:
        for u in G.nodes:
            e = d[u][v]
            g = query_distance(lables, v, u)
            if e != g:
                print("error: ", v, u, " except: ", e, " got: ", g)
                return
    print("ok.")
    # random_graph.print_graph(G)

def test_timecost():
    G = random_graph.random_graph(500, 0.3, 100)
    t1 = time.time()
    labels1 = weighted_pll(G)
    t2 = time.time()
    labels2 = list(nx.all_pairs_dijkstra(G))
    t3 = time.time()
    labels3 = nx.floyd_warshall(G)
    t4 = time.time()
    # print(labels1)
    # print(labels2)
    # print(labels3)

    print("weighted pll: ", t2 - t1)
    print("all pairs dij: ", t3 - t2)
    print("floyd warshall: ", t4 - t3)

def test_profile():
    G = random_graph.random_graph(1000, 0.3, 100)
    profile = lp.LineProfiler(weighted_pll)
    profile.add_function(pruned_dijkstra)
    profile.enable()
    weighted_pll(G)
    profile.disable()
    profile.print_stats()


# test_correctness()
test_timecost()
# test_profile()