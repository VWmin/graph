import pickle
import time
from multiprocessing import Pool
from multiprocessing.shared_memory import SharedMemory

import networkx as nx
import numpy as np

import random_graph

inf = 1000000000


def empty(G: nx.Graph, Lh):
    for v in G.nodes:
        if Lh[v]:
            return False
    return True


def PSL(G: nx.Graph):
    L = []
    L.append({v: {v: 0} for v in G.nodes})

    L.append({v: {} for v in G.nodes})
    for u, v in G.edges:
        if G.degree[u] > G.degree[v]:
            L[1][v][u] = 1
        else:
            L[1][u][v] = 1

    L.append({v: {} for v in G.nodes})
    h = 2

    while not empty(G, L[h - 1]):
        for v in G.nodes:
            cand = set()
            for u in G.neighbors(v):
                cand = cand | set(L[h - 1][u].keys())
            for w in cand:
                if G.degree[w] < G.degree[v]:
                    continue
                if Q_PSL(w, v, L, h) <= h:
                    continue
                L[h][v][w] = h
        L.append({v: {} for v in G.nodes})
        h = h + 1
    return L


def r(G: nx.Graph, u, v):
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
        cand = cand | set(L[h - 1][u].keys())
    for w in cand:
        if r(G, w, v):
            continue
        d = inf
        for u in G.neighbors(v):
            d = min(d, G[v][u]['weight'] + try_get(L[h - 1], u, w))
        if Q_WPSL(w, v, L, h) <= d:
            continue
        hack = L[h]
        hack[v][w] = d
        L[h] = hack


def WPSL(G: nx.Graph):
    L = []
    L.append({v: {v: 0} for v in G.nodes})

    h = 1
    while not empty(G, L[h - 1]):
        L.append({v: {} for v in G.nodes})

        # p = Pool()
        # for v in G.nodes:
        #     p.apply_async(func=step, args=(shm_G.name, shm_L, G.number_of_nodes, h, v))
        # p.close()
        # p.join()

        for v in G.nodes:
            step(G, L, h, v)

        h = h + 1
    return L


def multiprocess_step(shm_G, shm_G_size, shape, shm_L, shm_L_size, h, v):
    G_bytes = shm_G.buf[:shm_G_size]
    garr_from_bytes = np.frombuffer(G_bytes, dtype=np.float64).reshape(shape)
    G = nx.from_numpy_array(garr_from_bytes)

    L_bytes = shm_L.buf[:shm_L_size]
    L = pickle.loads(L_bytes)

    ans = {}

    cand = set()
    for u in G.neighbors(v):
        cand = cand | set(L[h - 1][u].keys())
    for w in cand:
        if r(G, w, v):
            continue
        d = inf
        for u in G.neighbors(v):
            d = min(d, G[v][u]['weight'] + try_get(L[h - 1], u, w))
        if Q_WPSL(w, v, L, h) <= d:
            continue
        ans[w] = d

    del G_bytes
    del garr_from_bytes
    del L_bytes
    return ans


def pow(x):
    t = time.time()
    print("time: {}, for {}".format(t, x))
    return x * x


def test_shared_memory_L(shm_L, shm_size):
    L_bytes = shm_L.buf[:shm_size]
    L = pickle.loads(L_bytes)
    print(L)
    del L_bytes
    shm_L.close()
    return 1


def test_shared_memory_G(shm_G, shm_size, shape):
    G_bytes = shm_G.buf[:shm_size]
    garr_from_bytes = np.frombuffer(G_bytes, dtype=np.float64).reshape(shape)
    G = nx.from_numpy_array(garr_from_bytes)
    print(G.edges)
    del G_bytes
    del garr_from_bytes
    shm_G.close()
    return 1


def multiprocess_WPSL(G: nx.Graph): \
        # 1. L <-> bytes
    # L = [{v:{v:0} for v in G.nodes}]
    # L_bytes = pickle.dumps(L)
    # L_from_bytes = pickle.loads(L_bytes)
    # print(L_from_bytes)

    # 2. G <-> bytes
    # garr = nx.to_numpy_array(G)
    # garr_bytes = garr.tobytes()
    # garr_from_bytes = np.frombuffer(garr_bytes, dtype=np.float64).reshape(garr.shape)
    # g = nx.from_numpy_array(garr_from_bytes)

    # 3. fire mutiprocess and get return value
    # with Pool() as p:
    #     res = p.map(pow, [1,2,3])
    #     print(res)

    # 4. shared memory L
    # L = [{v:{v:0} for v in G.nodes}]
    # L_bytes = pickle.dumps(L)
    # shm_L = SharedMemory(create=True, size=len(L_bytes))
    # shm_L.buf[:len(L_bytes)] = L_bytes
    # with Pool() as p:
    #     ans = p.starmap(test_shared_memory, [(shm_L, len(L_bytes)), (shm_L, len(L_bytes))])
    #     print(ans)
    #     p.close()
    #     p.join()
    # shm_L.close()
    # shm_L.unlink()

    # 5. shared memory G
    # garr = nx.to_numpy_array(G)
    # garr_bytes = garr.tobytes()
    # shm_G_size = len(garr_bytes)
    # shm_G = SharedMemory(create=True, size=shm_G_size)
    # shm_G.buf[:shm_G_size] = garr_bytes
    # n = G.number_of_nodes()
    # shape  = garr.shape
    # with Pool() as p:
    #     ans = p.starmap(test_shared_memory_G, [(shm_G, shm_G_size, shape), (shm_G, shm_G_size, shape)])
    #     print(ans)
    #     p.close()
    #     p.join()
    # print(G.edges)

    garr = nx.to_numpy_array(G)
    garr_bytes = garr.tobytes()
    shm_G_size = len(garr_bytes)
    shm_G = SharedMemory(create=True, size=shm_G_size)
    shm_G.buf[:shm_G_size] = garr_bytes
    shape = garr.shape

    L = [{v: {v: 0} for v in G.nodes}]
    h = 1
    while not empty(G, L[h - 1]):
        L.append({v: {} for v in G.nodes})

        L_bytes = pickle.dumps(L)
        shm_L_size = len(L_bytes)
        shm_L = SharedMemory(create=True, size=shm_L_size)
        shm_L.buf[:shm_L_size] = L_bytes

        with Pool() as p:
            ans = p.starmap(multiprocess_step, [(shm_G, shm_G_size, shape, shm_L, shm_L_size, h, v) for v in G.nodes])
            for v in range(len(ans)):
                for w in ans[v]:
                    L[h][v][w] = ans[v][w]

            p.close()
            p.join()

        del L_bytes
        shm_L.close()
        shm_L.unlink()
        h = h + 1
    del garr_bytes
    shm_G.close()
    shm_G.unlink()
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
        dis = min(dis, du[w] + dv[w])
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
        dis = min(dis, du[w] + dv[w])
    return dis


def example_graph():
    import numpy as np
    A = np.array([
        # 0  1  2  3  4  5  6  7  8  9 10
        [0, 0, 3, 0, 0, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 0, 4, 0],
        [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],  # 2
        [0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 1],  # 3
        [0, 1, 0, 0, 0, 3, 0, 0, 1, 0, 0],  # 4
        [0, 0, 0, 0, 3, 0, 0, 1, 1, 0, 0],  # 5
        [0, 0, 0, 3, 0, 0, 0, 0, 0, 8, 5],  # 6
        [2, 0, 0, 0, 0, 1, 0, 0, 2, 0, 4],  # 7
        [0, 0, 0, 0, 1, 1, 0, 2, 0, 5, 0],  # 8
        [0, 4, 0, 0, 0, 0, 8, 0, 5, 0, 3],  # 9
        [0, 0, 4, 1, 0, 0, 5, 4, 0, 3, 0],  # 10
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
    # G = example_graph()
    G = random_graph.random_graph(300, 0.1, 100)
    # Lwpsl = WPSL(G)
    Lwpsl = multiprocess_WPSL(G)

    import pll_weighted
    Lwpll = pll_weighted.weighted_pll(G)

    for u in G.nodes:
        for v in G.nodes:
            d1 = Q_WPSL(u, v, Lwpsl, len(Lwpsl))
            d2 = pll_weighted.query_distance(Lwpll, u, v)
            if d1 != d2:
                print("except {0}, got {1}, in {2}-{3}".format(d2, d1, u, v))
                # for i in range(len(Lwpsl)):
                #     print(Lwpsl[i])
                exit(0)
    print("all right")


def test_timecost_wpsl():
    import time
    G = random_graph.random_graph(100, 0.1, 100)
    # G = example_graph()

    t1 = time.time()
    Lwpsl = multiprocess_WPSL(G)

    t2 = time.time()
    print("WPSL time cost: {0}".format(t2 - t1))

    import pll_weighted
    Lwpll = pll_weighted.weighted_pll(G)
    t3 = time.time()
    print("WPLL time cost: {0}".format(t3 - t2))


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
    # multiprocess_WPSL(example_graph())
