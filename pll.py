import networkx as nx
import random_graph
import time
import line_profiler as lp

inf = 1000000000

def naive_landmark_labeling(G:nx.Graph):
    """
    Naive landmark labeling algorithm
    :param G: networkx graph, undirected, unweighted
    :return: landmark label dictionary
    """
    # initialize landmark label dictionary
    landmark_label = dict()
    def bfs(G:nx.Graph, root):
        distance = {}

        que = []
        que.append(root)
        distance[root] = 0
        while que:
            u = que.pop(0)
            for v in G.neighbors(u):
                if v not in distance:
                    distance[v] = distance[u] + 1
                    que.append(v)

        return distance

    # go through each vertices in G
    for v in G.nodes:
        landmark_label[v] = bfs(G, v)
    
    return landmark_label

def pruned_bfs(G:nx.Graph, vk, L, P, T):
    # L: {u:{v1:d1, v2, d2, ...}, u2:{...}, ...}
    que = [vk]
    P[vk] = 0
    visited = []

    while que:
        u = que.pop(0)
        visited.append(u)
        if pruned_query_distance(L, T, u) <= P[u]:
            continue
        # Lk[u] <- Lk_1[u] U {vk: P[u]}
        L[u][vk] = P[u]
        
        for w in G.neighbors(u):
            if P[w] == inf:
                P[w] = P[u] + 1
                que.append(w)
    for v in visited:
        P[v] = inf


def pruned_landmark_labeling(G:nx.Graph):
    L = {v:dict() for v in G.nodes}
    P = {v:inf for v in G.nodes}
    for v in G.nodes:
        T = {w:L[v][w] for w in L[v]}
        pruned_bfs(G, v, L, P, T)
    return L

def pruned_query_distance(L, T, u):
    distance = inf
    for w in L[u]:
        if w in T:
            distance = min(distance, L[u][w] + T[w])
    return distance
        

def query_distance(labels, u, v):
    if u not in labels or v not in labels:
        return inf
    distance = inf
    k = labels[u].keys() & labels[v].keys()
    for landmark in k:
        distance = min(distance, labels[u][landmark] + labels[v][landmark])
    return distance


def test_correctness():
    G = random_graph.random_graph(1000, 0.3, 100)
    # G = random_graph.demo_graph()
    t1 = time.time()
    # lables = naive_landmark_labeling(G)
    lables = pruned_landmark_labeling(G)
    t2 = time.time()
    print("naive_landmark_labeling: ", t2 - t1)

    d1 = query_distance(lables, 0, 7)
    t3 = time.time()
    print("d1: ", d1)
    print("cost1: ", t3 - t2)

    d2 = nx.shortest_path_length(G, 0, 7)
    t4 = time.time()
    print("d2: ", d2)
    print("cost2: ", t4 - t3)

    for v in G.nodes:
        for u in G.nodes:
            if query_distance(lables, v, u) != nx.shortest_path_length(G, v, u):
                print("error: ", v, u)
                break
    print("done")
    # random_graph.print_graph(G)

def test_timecost():
    G = random_graph.random_graph(1000, 0.3, 100)
    t1 = time.time()
    labels1 = pruned_landmark_labeling(G)
    t2 = time.time()
    # labels2 = naive_landmark_labeling(G)
    t3 = time.time()
    # print(labels1)
    # print(labels2)

    print("pruned_landmark_labeling: ", t2 - t1)
    print("naive_landmark_labeling: ", t3 - t2)

def test_profile():
    G = random_graph.random_graph(1000, 0.3, 100)
    profile = lp.LineProfiler(pruned_landmark_labeling)
    profile.add_function(pruned_query_distance)
    profile.add_function(pruned_bfs)
    profile.enable()
    pruned_landmark_labeling(G)
    profile.disable()
    profile.print_stats()


# test_correctness()
test_timecost()
# test_profile()