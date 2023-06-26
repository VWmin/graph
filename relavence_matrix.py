import random_graph
import networkx as nx
import random
import numpy as np

def relavence_matrix(G:nx.Graph, distance, D, S2R):
    n = G.number_of_nodes()
    # initialize relavence matrix
    relavence = [[set() for i in range(n)] for j in range(n)]
    # fill relavence matrix O(EV^2)
    for edge in list(G.edges):
        i, j = edge
        i, j =  (j, i) if (i > j) else (i, j)
        for s in S2R:
            R = S2R[s]
            for r in R:
                if distance[s][i] + G[i][j]['weight'] + distance[j][r] <= D[s]:
                    relavence[i][j].add(s)
    return relavence

def improved_relavence_matrix(G:nx.Graph, D, S2R):
    n = G.number_of_nodes()
    # initialize relavence matrix
    relavence = [[set() for i in range(n)] for j in range(n)]
    for s in S2R:
        for r in S2R[s]:
            paths = all_simple_paths_cutoff_weight(G, s, r, D[s])
            for path in paths:
                for i in range(len(path)-1):
                    relavence[path[i]][path[i+1]].add(s)
    return relavence

def all_simple_paths_cutoff_weight(G, source, target, cutoff):
    # parameters check
    if source not in G:
        raise nx.NodeNotFound(f"source node {source} not in graph")
    if target in G:
        targets = {target}
    else:
        try:
            targets = set(target)
        except TypeError as err:
            raise nx.NodeNotFound(f"target node {target} not in graph") from err
    if source in targets:
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
    

def KMB(G:nx.Graph, terminals):
    # 1. dis[s][r] <- dijsktra
    # dis = {}
    # for s in S2R:
    #     R = S2R[s]
    #     for r in R:
    #         dis[s][r] = nx.single_source_dijkstra(G, s, r)
    # 1. get G1
    dis = {}
    for t in terminals:
        dis[t] = nx.single_source_dijkstra(G, t)
    G1 = nx.Graph()
    for t in terminals:
        for t2 in terminals:
            if t == t2:
                continue
            G1.add_edge(t, t2, weight=dis[t][0][t2])
            

    # 2. prime G1
    
    T1E = nx.minimum_spanning_edges(G1, data=False)

    # 3. recover Gs
    Gs = nx.Graph()
    for edge in sorted(sorted(e) for e in list(T1E)):
        i, j = edge
        path = dis[i][1][j]
        for k in range(len(path)-1):
            Gs.add_edge(path[k], path[k+1], weight=G[path[k]][path[k+1]]['weight'])
    
    # 4. prime Ts
    Ts = nx.minimum_spanning_tree(Gs)

    # 5. reserve terminals - remove any leaf that not in terminals
    # 5.1 collect leafs
    target = set(terminals)
    leafs = set()
    for node in Ts.nodes:
        if Ts.degree(node) == 1:
            leafs.add(node)
    # 5.2 remove leaf and edge not realated to terminals
    while leafs != target:
        for node in leafs:
            if node not in target:
                next = node
                while next:
                    neighbors = list(Ts.neighbors(next))
                    Ts.remove_node(next)
                    next = neighbors[0] if len(neighbors) == 1 else None
    return Ts

def random_S(n, p):
    if p<0 or p>1:
        p = 0.1
    aim = int(n * p)
    S = []
    while len(S) < aim:
        s = random.randint(0, n-1)
        if s not in S:
            S.append(s)
    return S

def random_S2R(n, S, p):
    if p<0 or p>1:
        p = 0.1
    S2R = {}
    aim = int(n * p)
    cnt = 0
    while cnt < aim:
        r = random.randint(0, n-1)
        if r in S:
            continue
        s = random.choice(S)
        S2R[s] = S2R.get(s, []) + [r]
        cnt += 1
    return S2R

def general_floyd(G:nx.Graph):
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

def random_D(S, w):
    D = {}
    for s in S:
        D[s] = random.randint(2*w, 5*w)
    return D



