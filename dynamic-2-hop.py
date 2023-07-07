import networkx as nx
import random_graph
import numpy as np
from multiprocessing import Pool
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.managers import SharedMemoryManager
import pickle

inf = 1000000000

def empty(G:nx.Graph, Lh):
    for v in G.nodes:
        if Lh[v]:
            return False
    return True

def PSL(G:nx.Graph):
    L = []
    L.append( {v:{v:0} for v in G.nodes} )
    
    L.append({v:{} for v in G.nodes})
    for u, v in G.edges:
        if G.degree[u] > G.degree[v]:
            L[1][v][u] = 1
        else:
            L[1][u][v] = 1
    
    L.append({v:{} for v in G.nodes})
    h = 2
    
    while not empty(G, L[h-1]):
        for v in G.nodes:
            cand = set()
            for u in G.neighbors(v):
                cand = cand | set(L[h-1][u].keys())
            for w in cand:
                if G.degree[w] < G.degree[v]:
                    continue
                if Q_PSL(w, v, L, h) <= h:
                    continue
                L[h][v][w] = h
        L.append({v:{} for v in G.nodes})
        h = h+1
    return L


def r(G:nx.Graph, u, v):
        if G.degree[u] == G.degree[v]:
            return u < v
        return G.degree[u] < G.degree[v]

def try_get(Lh, u, w):
        if w not in Lh[u]:
            return inf
        return Lh[u][w]

def step(G, L, h, v):
    cand = set()
    for u in G.neighbors(v):
        cand = cand | set(L[h-1][u].keys())
    for w in cand:
        if r(G, w, v):
            continue
        d = inf
        for u in G.neighbors(v):
            d = min(d, G[v][u]['weight']+try_get(L[h-1], u, w))
        if Q_WPSL(w, v, L, h) <= d:
            continue
        hack = L[h]
        hack[v][w] = d
        L[h] = hack

def WPSL(G:nx.Graph):
    L = []
    L.append({v:{v:0} for v in G.nodes})

    h = 1
    while not empty(G, L[h-1]):
        L.append({v:{} for v in G.nodes})
        
        # p = Pool()
        # for v in G.nodes:
        #     p.apply_async(func=step, args=(shm_G.name, shm_L, G.number_of_nodes, h, v))
        # p.close()
        # p.join()

        for v in G.nodes:
            step(G, L, h, v)

        h = h+1
    return L

def Q_PSL(u, v, L, h):
    dis = inf
    du, dv = {}, {}
    for i in range(h):
        for w in L[i][u]:
            du[w] = i
        for w in L[i][v]:
            dv[w] = i
    for w in du.keys() & dv.keys():
        dis = min(dis, du[w]+dv[w])
    return dis

def Q_WPSL(u, v, L, h):
    dis = inf
    du, dv = {}, {}
    for i in range(h):
        for w in L[i][u]:
            du[w] = L[i][u][w]
        for w in L[i][v]:
            dv[w] = L[i][v][w]
    for w in du.keys() & dv.keys():
        dis = min(dis, du[w]+dv[w])
    return dis


def example_graph():
    import numpy as np
    A = np.array([
        #0  1  2  3  4  5  6  7  8  9 10
        [0, 0, 3, 0, 0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 4, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4], #2
        [0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 1], #3
        [0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0], #4
        [0, 0, 0, 0, 3, 0, 0, 1, 1, 0, 0], #5
        [0, 0, 0, 3, 0, 0, 0, 0, 0, 8, 5], #6
        [2, 0, 0, 0, 0, 1, 0, 0, 2, 0, 4], #7
        [0, 0, 0, 0, 1, 1, 0, 2, 0, 5, 0], #8
        [0, 4, 0, 0, 0, 0, 8, 0, 5, 0, 3], #9
        [0, 0, 4, 1, 0, 0, 5, 4, 0, 3, 0], #10
        ])
    G = nx.from_numpy_array(A)
    return G


def test_correctness_psl():
    G = example_graph()
    Lpsl = PSL(G)

    import pll
    Lpll = pll.pruned_landmark_labeling(G)

    for u in G.nodes:
        for v in G.nodes:
            d1 = Q_PSL(u, v, Lpsl, len(Lpsl))
            d2 = pll.query_distance(Lpll, u, v)
            if d1 != d2:
                print("except {0}, got {1}", d2, d1)
                exit(0)
    print("all right")

def test_correctness_wpsl():
    G = example_graph()
    # G = random_graph.random_graph(300, 0.1, 100)
    Lwpsl = WPSL(G)

    import pll_weighted
    Lwpll = pll_weighted.weighted_pll(G)

    for u in G.nodes:
        for v in G.nodes:
            d1 = Q_WPSL(u, v, Lwpsl, len(Lwpsl))
            d2 = pll_weighted.query_distance(Lwpll, u, v)
            if d1 != d2:
                print("except {0}, got {1}, in {2}-{3}".format(d2, d1, u, v))
                for i in range(len(Lwpsl)):
                    print(Lwpsl[i])
                exit(0)
    print("all right")

def test_timecost_wpsl():
    import time
    G = random_graph.random_graph(300, 0.1, 100)
    # G = example_graph()

    t1 = time.time()
    Lwpsl = WPSL(G)

    t2 = time.time()
    print("WPSL time cost: {0}".format(t2-t1))

    import pll_weighted
    Lwpll = pll_weighted.weighted_pll(G)
    t3 = time.time()
    print("WPLL time cost: {0}".format(t3-t2))

def test_profile_wpsl():
    import line_profiler as lp
    G = random_graph.random_graph(300, 0.1, 100)
    profile = lp.LineProfiler(WPSL)
    profile.add_function(Q_WPSL)
    profile.enable()
    WPSL(G)
    profile.disable()
    profile.print_stats()


if __name__ == "__main__":
    # test_correctness_wpsl()
    test_timecost_wpsl()
    # test_profile_wpsl()
