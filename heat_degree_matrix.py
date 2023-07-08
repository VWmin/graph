import networkx as nx
import time

import pll_weighted
import random_graph
import relavence_matrix


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


def heat_degree_matrix(relavence, G:nx.Graph, Ex, s, r):
    # max_w = 0
    # V = G.number_of_nodes()
    # for u, v, w in G.edges.data('weight'):
    #     max_w = max(max_w, w)
    #
    # def heat_degree_matrix_ij(Ts, i, j):
    #     # 如果边ij是s的候选边，且已在以s为源的现存多播树中
    #     # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
    #     if s in relavence[i][j]:
    #         if G[i][j] in Ts or checkB():
    #             return 'case1'
    #         else:
    #             return 'case2'
    #     else :
    #         return 'case3'
    pass


if __name__ == '__main__':
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

