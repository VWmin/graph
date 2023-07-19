import networkx as nx
import time

import pll_weighted
import random_graph
import relavence_matrix

inf = 1000000000


def relevance_matrix_with_wpll(G:nx.Graph, D, S2R):
    n = G.number_of_nodes()
    labels = pll_weighted.weighted_pll(G)
    relevance = [[set() for _ in range(n)] for _ in range(n)]

    for i, j in G.edges:
        i, j = (j, i) if i > j else (i, j)
        for s in S2R:
            for r in S2R[s]:
                if pll_weighted.query_distance(labels, s, i) + G[i][j]['weight'] + pll_weighted.query_distance(labels, j, r) <= D[s]:
                    relevance[i][j].add(s)
    return relevance


def heat_degree_matrix(relavence, G:nx.Graph, S, D, B):
    max_ld = 0
    V = G.number_of_nodes()
    for _, _, w in G.edges.data('weight'):
        max_ld = max(max_ld, w)

    def checkB(u, v):
        # 检查边uv的带宽是否满足所有以其为候选边的源的带宽要求之和
        u, v = (v, u) if u > v else (u, v)
        sum = 0
        for s in relavence[u][v]:
            sum += B[s]
        return (sum, sum <= G[u][v]['bandwidth'])

    
    def heat_degree_matrix_ij(i, j):
        # 如果边ij是s的候选边，且已在以s为源的现存多播树中
        # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
        if relavence[i][j]:
            sum, satisify = checkB(i, j)
            if satisify:
                return G[i][j]['weight'] / (V*max_ld)
            else:
                return pow(sum/G[i][j]['bandwidth'], 2)
        else:
            return inf
    heat = [[heat_degree_matrix_ij(i, j) for j in range(V)] for i in range(V)]
    return heat

def heat_matrix_based_routing(heat, G:nx.Graph, S2R):
    for u, v in G.edges:
        G[u][v]['heat'] = heat[u][v]
    for s in S2R:
        Ts = {s}
        for r in S2R[s]:
            cost, path = nx.multi_source_dijkstra(G, Ts, target=r, weight='heat')
            for i in path: Ts.add(i)
            print(f"heat_matrix_based_routing: {s} -> {r}: {path}")

def test_relevance_run_time():
    n = 500
    p_edge = 0.1
    w_range = 100
    p_s = 0.1
    p_r = 0.1

    G = random_graph.random_graph(n, p_edge, w_range)
    S = relavence_matrix.random_S(n, p_s)
    S2R = relavence_matrix.random_S2R(n, S, p_r)
    D = relavence_matrix.random_D(S, w_range)

    t1 = time.time()

    relevance_matrix_with_wpll(G, D, S2R)
    t2 = time.time()
    print(f"relevance_matrix_with_wpll: {t2-t1}")

    distance = relavence_matrix.general_floyd(G)
    relavence_matrix.relavence_matrix(G, distance, D, S2R)
    t3 = time.time()
    print(f"relavence_matrix: {t3-t2}")

if __name__ == '__main__':
    number_of_nodes = 2000
    prob_of_edge = 0.1
    weight_range = 100
    prob_of_src = 0.1
    prob_of_recv = 0.1
    bandwidth_range = 100

    G = random_graph.random_graph(number_of_nodes, prob_of_edge, weight_range)
    relavence_matrix.add_random_bandwidth_attr(G, bandwidth_range)
    S = relavence_matrix.random_S(number_of_nodes, prob_of_src)
    S2R = relavence_matrix.random_S2R(number_of_nodes, S, prob_of_recv)
    D = relavence_matrix.random_D(S, weight_range) # Delay limit of each source
    B = relavence_matrix.random_B(S, bandwidth_range) # Bandwidth requirement of each source

    t1 = time.time()
    # distance = relavence_matrix.general_floyd(G)
    distance = nx.floyd_warshall_numpy(G)
    relevance = relavence_matrix.relavence_matrix(G, distance, D, S2R)
    heat = heat_degree_matrix(relevance, G, S, D, B)
    heat_matrix_based_routing(heat, G, S2R)
    t2 = time.time()
    print(f"heat_matrix_based_routing: {t2-t1}s")

    

