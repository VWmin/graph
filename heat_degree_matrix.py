import networkx as nx
import time

import pll_weighted
import random_graph
import relavence_matrix

inf = 1000000000


class HeatDegreeModel:
    def __init__(self, g: nx.graph, delay_limit, bandwidth_require, src2recv):
        self.g = g
        self.delay_limit = delay_limit
        self.bandwidth_require = bandwidth_require
        self.src2recv = src2recv
        self.__build_relevance__()
        self.__build_heat_matrix__()
        self.__routing__()

    def __build_relevance__(self):
        n = self.g.number_of_nodes()
        labels = pll_weighted.weighted_pll(self.g)
        sp = pll_weighted.query_distance
        self.relevance = [[set() for _ in range(n)] for _ in range(n)]

        for i, j in self.g.edges:
            i, j = (j, i) if i > j else (i, j)
            for s in self.src2recv:
                for r in self.src2recv[s]:
                    if sp(labels, s, i) + self.g[i][j]['weight'] + sp(
                            labels, j, r) <= self.delay_limit[s]:
                        self.relevance[i][j].add(s)

    def __build_heat_matrix__(self):
        max_delay = self.get_max_delay()
        n = self.g.number_of_nodes()

        def heat_degree_matrix_ij(i, j):
            # 如果边ij是s的候选边，且已在以s为源的现存多播树中
            # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
            if self.relevance[i][j]:
                _sum, ok = self.check_bandwidth_limit(i, j)
                if ok:
                    return self.g[i][j]['weight'] / (n * max_delay)
                else:
                    return pow(_sum / self.g[i][j]['bandwidth'], 2)
            else:
                return inf

        self.heat = [[heat_degree_matrix_ij(i, j) for j in range(n)] for i in range(n)]
        for u, v in self.g.edges:
            self.g[u][v]['heat'] = self.heat[u][v]

    def __routing__(self):
        self.T = {}
        for s in self.src2recv:
            self.T[s] = {}
            for r in self.src2recv[s]:
                _, path = nx.single_source_dijkstra(self.g, s, target=r, weight='heat')
                self.T[s][r] = path

    def check_bandwidth_limit(self, u, v):
        u, v = (v, u) if u > v else (u, v)
        _sum = 0
        for s in self.relevance[u][v]:
            _sum += self.bandwidth_require[s]
        return _sum, _sum <= self.g[u][v]['bandwidth']

    def get_max_delay(self):
        return max(dict(self.g.edges).items(), key=lambda x: x[1]['weight'])


def relevance_matrix_with_wpll(G: nx.Graph, D, S2R):
    n = G.number_of_nodes()
    labels = pll_weighted.weighted_pll(G)
    query = pll_weighted.query_distance
    relevance = [[set() for _ in range(n)] for _ in range(n)]

    for i, j in G.edges:
        i, j = (j, i) if i > j else (i, j)
        for s in S2R:
            for r in S2R[s]:
                if query(labels, s, i) + G[i][j]['weight'] + query(labels, j, r) <= D[s]:
                    relevance[i][j].add(s)
    return relevance


def heat_degree_matrix(relavence, G: nx.Graph, S, D, B):
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
                return G[i][j]['weight'] / (V * max_ld)
            else:
                return pow(sum / G[i][j]['bandwidth'], 2)
        else:
            return inf

    heat = [[heat_degree_matrix_ij(i, j) for j in range(V)] for i in range(V)]
    return heat


def heat_matrix_based_routing(heat, G: nx.Graph, S2R):
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
    print(f"relevance_matrix_with_wpll: {t2 - t1}")

    distance = relavence_matrix.general_floyd(G)
    relavence_matrix.relavence_matrix(G, distance, D, S2R)
    t3 = time.time()
    print(f"relavence_matrix: {t3 - t2}")


def test_heat_matrix_based_routing():
    number_of_nodes = 200
    prob_of_edge = 0.1
    weight_range = 100
    prob_of_src = 0.1
    prob_of_recv = 0.1
    bandwidth_range = 100

    G = random_graph.random_graph(number_of_nodes, prob_of_edge, weight_range)
    relavence_matrix.add_random_bandwidth_attr(G, bandwidth_range, .9, 1.1)
    S = relavence_matrix.random_S(number_of_nodes, prob_of_src)
    S2R = relavence_matrix.random_S2R(number_of_nodes, S, prob_of_recv)
    D = relavence_matrix.random_D(S, weight_range)  # Delay limit of each source
    B = relavence_matrix.random_B(S, bandwidth_range, .2, .5)  # Bandwidth requirement of each source

    t1 = time.time()
    # distance = relavence_matrix.general_floyd(G)
    distance = nx.floyd_warshall_numpy(G)
    relevance = relavence_matrix.relavence_matrix(G, distance, D, S2R)
    heat = heat_degree_matrix(relevance, G, S, D, B)
    heat_matrix_based_routing(heat, G, S2R)
    t2 = time.time()
    print(f"heat_matrix_based_routing: {t2 - t1}s")


def test_member_change():
    number_of_nodes = 30
    prob_of_edge = 0.1
    weight_range = 100
    S = relavence_matrix.random_single_s(number_of_nodes)
    prob_of_recv = 0.2
    bandwidth_range = 100

    G = random_graph.random_graph(number_of_nodes, prob_of_edge, weight_range)
    relavence_matrix.add_random_bandwidth_attr(G, bandwidth_range, .5, .5)
    S2R = relavence_matrix.random_S2R(number_of_nodes, S, prob_of_recv)
    D = relavence_matrix.random_D(S, weight_range)  # Delay limit of each source
    B = relavence_matrix.random_B(S, bandwidth_range, .4, .4)  # Bandwidth requirement of each source

    distance = nx.floyd_warshall_numpy(G)
    relevance = relavence_matrix.relavence_matrix(G, distance, D, S2R)
    heat1 = heat_degree_matrix(relevance, G, S, D, B)

    import random
    # add = random.randint(0, 1)
    add = 1
    heat2 = None
    heat3 = None
    if add == 1:
        r = random.randint(0, number_of_nodes - 1)
        while r in S2R[S[0]] or r == S[0]:
            r = random.randint(0, number_of_nodes - 1)
        S2R[S[0]] = S2R.get(S[0], []) + [r]

        relevance3 = relavence_matrix.relavence_matrix(G, distance, D, S2R)
        heat3 = heat_degree_matrix(relevance3, G, S, D, B)

    print(f"S: {S[0]}\tR: {S2R[S[0]]}\tr: {r}\toperation: {'add' if add else 'delete'}\n")

    for i in range(len(heat1)):
        for j in range(len(heat1[i])):
            if heat1[i][j] == inf: continue
            print(
                f"heat1[{i}][{j}]: {heat1[i][j]}\theat3[{i}][{j}]: {heat3[i][j]}\tdiff: {heat1[i][j] != heat3[i][j]}\n")


def test_model():
    number_of_nodes = 200
    prob_of_edge = 0.1
    weight_range = 100
    prob_of_src = 0.1
    prob_of_recv = 0.1
    bandwidth_range = 100

    G = random_graph.random_graph(number_of_nodes, prob_of_edge, weight_range)
    relavence_matrix.add_random_bandwidth_attr(G, bandwidth_range, .9, 1.1)
    S = relavence_matrix.random_S(number_of_nodes, prob_of_src)
    S2R = relavence_matrix.random_S2R(number_of_nodes, S, prob_of_recv)
    D = relavence_matrix.random_D(S, weight_range)  # Delay limit of each source
    B = relavence_matrix.random_B(S, bandwidth_range, .2, .5)  # Bandwidth requirement of each source

    model = HeatDegreeModel(G, D, B, S2R)


if __name__ == '__main__':
    test_model()
    # test_relevance_run_time()
    # test_member_change()
    # test_heat_matrix_based_routing()
