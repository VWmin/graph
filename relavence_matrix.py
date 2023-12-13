import random_graph
import networkx as nx
import random
import numpy as np
import time


def relavence_matrix(G: nx.Graph, distance, D, S2R):
    n = G.number_of_nodes()
    # initialize relavence matrix
    relavence = [[set() for i in range(n)] for j in range(n)]
    # fill relavence matrix O(EV^2)
    for edge in list(G.edges):
        i, j = edge
        i, j = (j, i) if (i > j) else (i, j)
        for s in S2R:
            R = S2R[s]
            for r in R:
                if distance[s][i] + G[i][j]['weight'] + distance[j][r] <= D[s]:
                    relavence[i][j].add(s)
    return relavence


def relavence_matrix_without_distance(G: nx.Graph, D, S2R):
    n = G.number_of_nodes()
    relavence = [[set() for i in range(n)] for j in range(n)]
    for edge in list(G.edges):
        i, j = edge
        i, j = (j, i) if (i > j) else (i, j)
        for s in S2R:
            R = S2R[s]
            for r in R:
                if nx.dijkstra_path_length(G, s, i) + G[i][j]['weight'] + nx.dijkstra_path_length(G, j, r) <= D[s]:
                    relavence[i][j].add(s)
    return relavence


def relevance_matrix_with_wpll(G: nx.Graph, D, S2R):
    import pll_weighted
    n = G.number_of_nodes()
    labels = pll_weighted.weighted_pll(G)
    relevance = [[set() for _ in range(n)] for _ in range(n)]

    for i, j in G.edges:
        i, j = (j, i) if i > j else (i, j)
        for s in S2R:
            for r in S2R[s]:
                if pll_weighted.query_distance(labels, s, i) + G[i][j]['weight'] + pll_weighted.query_distance(labels,
                                                                                                               j, r) <= \
                        D[s]:
                    relevance[i][j].add(s)
    return relevance


def improved_relavence_matrix(G: nx.Graph, D, S2R):
    n = G.number_of_nodes()
    # initialize relavence matrix
    relavence = [[set() for i in range(n)] for j in range(n)]
    for s in S2R:
        paths = all_simple_paths_cutoff_weight(G, s, set(S2R), D[s])
        for path in paths:
            for i in range(len(path) - 1):
                x, y = path[i], path[i + 1]
                x, y = (y, x) if (x > y) else (x, y)
                relavence[x][y].add(s)
    return relavence


def all_simple_paths_cutoff_weight(G, source, targets: set, cutoff):
    # parameters check
    if source not in G:
        raise nx.NodeNotFound(f"source node {source} not in graph")
    for target in targets:
        if target not in G:
            raise nx.NodeNotFound(f"target node {target} not in graph")
    if source in targets:
        if len(targets) != 1:
            targets = targets - {source}
        else:
            return nx._empty_generator()

    # dfs
    visited = {source: True}
    stack = [(source, iter(G[source]))]
    used_w = []
    sum = 0
    while stack:
        cur, children = stack[-1]
        # 当前节点的下一个节点
        child = next(children, None)
        # print(cur, child)
        # 当前节点相邻的节点都已经访问过了
        if child is None:
            if len(used_w) > 0:
                sum -= used_w[-1]
                used_w.pop()
            stack.pop()
            visited.popitem()
        # 进入下一个节点前，花销满足
        elif sum <= cutoff:
            if child in visited or sum + G[cur][child]['weight'] > cutoff:
                continue
            sum += G[cur][child]['weight']
            used_w.append(G[cur][child]['weight'])
            if child in targets:
                yield list(visited) + [child]
            visited[child] = True
            if targets - set(visited.keys()):  # expand stack until find all targets
                stack.append((child, iter(G[child])))
            else:
                visited.popitem()  # maybe other ways to child
                sum -= used_w[-1]
                used_w.pop()


def dfs(G, source, target, cutoff):
    visited = {source: True}

    def _dfs_(G, cur, sum, cutoff):
        if sum > cutoff:
            return
        if cur == target:
            yield list(visited)
        for child in G[cur]:
            if child in visited:
                continue
            visited[child] = True
            yield from _dfs_(G, child, sum + G[cur][child]['weight'], cutoff)
            visited.popitem()

    yield from _dfs_(G, source, 0, cutoff)


def weight_function(G: nx.Graph, u, v, weight):
    if callable(weight):
        return weight(u, v, G[u][v])
    return G[u][v][weight]


def KMB(G: nx.Graph, terminals, weight='weight'):
    # 1. dis[s][r] <- dijsktra
    # dis = {}
    # for s in S2R:
    #     R = S2R[s]
    #     for r in R:
    #         dis[s][r] = nx.single_source_dijkstra(G, s, r)
    # 1. get G1
    # t0 = time.time()
    dis = {}
    G1 = nx.Graph()
    for i in range(len(terminals)):
        paths = nx.single_source_dijkstra(G, terminals[i], weight=weight)
        for j in range(i + 1, len(terminals)):
            ii, jj = terminals[i], terminals[j]
            if ii not in dis:
                dis[ii] = {}
            dis[ii][jj] = (paths[0][jj], paths[1][jj])
            G1.add_edge(ii, jj, weight=dis[ii][jj][0])

    # t1 = time.time()
    # print("G1 cost: ", t1 - t0)

    # 2. prime G1
    T1E = nx.minimum_spanning_edges(G1, data=False)
    # t2 = time.time()
    # print("prime G1 cost: ", t2 - t1)

    # 3. recover Gs
    Gs = nx.Graph()
    for edge in list(T1E):
        i, j = edge
        path = dis[i][j][1]
        for k in range(len(path) - 1):
            u, v = path[k], path[k + 1]
            Gs.add_edge(u, v, weight=weight_function(G, u, v, weight))
    # t3 = time.time()
    # print("recover Gs cost: ", t3 - t2)

    # 4. prime Ts
    Ts = nx.minimum_spanning_tree(Gs)
    # t4 = time.time()
    # print("prime Ts cost: ", t4 - t3)

    # 5. reserve terminals - remove any leaf that not in terminals
    # 5.1 collect leafs
    target = set(terminals)
    leafs = set()
    for node in Ts.nodes:
        if Ts.degree(node) == 1:
            leafs.add(node)
    leafs = leafs - target
    # 5.2 remove leaf and edge not realated to terminals
    for node in leafs:
        # print("terminals: ", target, ", leafs: ", leafs,  ", checking node: ", node)
        _next = node
        while _next:
            neighbors = list(Ts.neighbors(_next))
            Ts.remove_node(_next)
            _next = neighbors[0] if len(neighbors) == 1 else None
    # t5 = time.time()
    # print("reserve terminals cost: ", t5 - t4)
    return Ts


def random_S(n, p):
    if p < 0 or p > 1:
        p = 0.1
    aim = int(n * p)
    S = []
    while len(S) < aim:
        s = random.randint(0, n - 1)
        if s not in S:
            S.append(s)
    return S


def random_single_s(n):
    s = random.randint(0, n - 1)
    return [s]


def random_S2R(n, S, p):
    if p < 0 or p > 1:
        p = 0.1
    S2R = {}
    aim = int(n * p)
    cnt = 0
    while cnt < aim:
        r = random.randint(0, n - 1)
        if r in S:
            continue
        s = random.choice(S)
        S2R[s] = S2R.get(s, set()) | {r}
        cnt += 1
    return S2R


def general_floyd(G: nx.Graph):
    A = nx.to_numpy_array(
        G, None, multigraph_weight=min, nonedge=np.inf
    )
    n, m = A.shape
    np.fill_diagonal(A, 0)
    for k in range(n):
        for i in range(n):
            for j in range(n):
                A[i][j] = min(A[i][j], A[i][k] + A[k][j])
    # for i in range(n):
    #     # The second term has the same shape as A due to broadcasting
    #     A = np.minimum(A, A[i, :][np.newaxis, :] + A[:, i][:, np.newaxis])
    return A


def general_floyd2(G: nx.Graph, weight="weight"):
    from collections import defaultdict

    # dictionary-of-dictionaries representation for dist and pred
    # use some defaultdict magick here
    # for dist the default is the floating point inf value
    dist = defaultdict(lambda: defaultdict(lambda: float("inf")))
    for u in G:
        dist[u][u] = 0
    # initialize path distance dictionary to be the adjacency matrix
    # also set the distance to self to 0 (zero diagonal)
    undirected = not G.is_directed()
    for u, v, d in G.edges(data=True):
        e_weight = d.get(weight, 1.0)
        dist[u][v] = min(e_weight, dist[u][v])
        if undirected:
            dist[v][u] = min(e_weight, dist[v][u])
    for w in G:
        dist_w = dist[w]  # save recomputation
        for u in G:
            dist_u = dist[u]  # save recomputation
            for v in G:
                d = dist_u[w] + dist_w[v]
                if dist_u[v] > d:
                    dist_u[v] = d
    return dict(dist)


def random_D(S, w):
    D = {}
    for s in S:
        D[s] = random.randint(2 * w, 5 * w)
    return D


def random_B(S, b, lower_p, upper_p):
    B = {}
    for s in S:
        B[s] = random.randint(int(lower_p * b), int(upper_p * b))
    return B


def add_random_bandwidth_attr(G, b, lower_p, upper_p):
    for u, v in G.edges:
        G[u][v]['bandwidth'] = random.randint(int(lower_p * b), int(upper_p * b))


def test_relaven_run_time():
    n, p, w = 200, 0.3, 100
    G = random_graph.random_graph(n, p, w)
    S2R = random_S2R(n, random_S(n, 0.1), 0.2)
    D = random_D(S2R.keys(), w)

    t1 = time.time()

    relavence1 = relavence_matrix_without_distance(G, D, S2R)
    t2 = time.time()
    print("base: ", t2 - t1)

    relavence2 = relevance_matrix_with_wpll(G, D, S2R)
    t3 = time.time()
    print("method: ", t3 - t2)

    print(relavence1 == relavence2)


if __name__ == "__main__":
    # test_relaven_run_time()
    import networkx as nx
    import matplotlib.pyplot as plt

    # 创建一个有向图
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 4), (4, 5)])

    t = map(lambda e: e*2, list(G.successors(1)))
    print(list(t))

