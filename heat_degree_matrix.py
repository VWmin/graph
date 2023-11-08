import networkx as nx
import time

import pll_weighted
import random_graph
import relavence_matrix
from math import inf


class HeatDegreeModel:
    def __init__(self, g: nx.graph, delay_limit, bandwidth_require, src2recv):
        self.g = g
        self.delay_limit = delay_limit
        self.bandwidth_require = bandwidth_require
        self.src2recv = src2recv
        self.use_pll = True
        self.routing_trees = {}
        self.__labels__ = 0
        self.__distance__ = 0
        self.__build_relevance__()
        self.__build_heat_matrix__()
        self.__routing__()

    def __build_relevance__(self):
        n = self.g.number_of_nodes()
        self.relevance = [[set() for _ in range(n)] for _ in range(n)]

        for i, j in self.g.edges:
            i, j = (j, i) if i > j else (i, j)
            for s in self.src2recv:
                for r in self.src2recv[s]:
                    if self.query(s, i) + self.g[i][j]['weight'] + self.query(j, r) <= self.delay_limit[s]:
                        self.relevance[i][j].add(s)

    def __build_heat_matrix__(self):
        max_delay = self.get_max_delay()
        n = self.g.number_of_nodes()

        def heat_degree_matrix_ij(s, i, j):
            # 如果边ij是s的候选边，且已在以s为源的现存多播树中
            # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
            if s in self.relevance[i][j]:
                ok1 = self.__is_routing_contains_edge__(s, i, j)
                _sum, ok2 = self.check_bandwidth_limit(i, j)
                if ok1 or ok2:
                    return self.g[i][j]['weight'] / (n * max_delay)
                else:
                    return pow(_sum / self.g[i][j]['bandwidth'], 2)
            else:
                return inf

        self.heat = {}
        for src in self.src2recv:
            self.heat[src] = [[heat_degree_matrix_ij(src, i, j) for j in range(n)] for i in range(n)]

    def __routing__(self):
        for s in self.src2recv:
            self.routing_trees[s] = {}
            for r in self.src2recv[s]:
                _, path = nx.single_source_dijkstra(self.g, s, target=r, weight=lambda u, v, d: self.heat[s][u][v])
                self.routing_trees[s][r] = path

    def __pll_query__(self, u, v):
        if self.__labels__ == 0:
            self.__labels__ = pll_weighted.weighted_pll(self.g)
        return pll_weighted.query_distance(self.__labels__, u, v)

    def __distance_query(self, u, v):
        if self.__distance__ == 0:
            self.__distance__ = nx.floyd_warshall_numpy(self.g)
        return self.__distance__[u][v]

    def __is_routing_contains_edge__(self, s, u, v) -> bool:
        if s not in self.routing_trees:
            return False
        for i in range(1, len(self.routing_trees[s])):
            a, b = self.routing_trees[s][i-1], self.routing_trees[s][i]
            if (a, b) == (u, v) or (b, a) == (u, v):
                return True
        return False

    def query(self, u, v):
        if self.use_pll:
            return self.__pll_query__(u, v)
        else:
            return self.__distance_query(u, v)

    def check_bandwidth_limit(self, u, v):
        u, v = (v, u) if u > v else (u, v)
        _sum = 0
        for s in self.relevance[u][v]:
            _sum += self.bandwidth_require[s]
        return _sum, _sum <= self.g[u][v]['bandwidth']

    def get_max_delay(self):
        return max(dict(self.g.edges).items(), key=lambda x: x[1]['weight'])

    def add_recv(self, s, r):
        self.src2recv[s].append(r)
        updated = set()
        for u, v in self.g.edges:
            u, v = (v, u) if u > v else (u, v)
            if (self.query(s, u)+self.g[u][v]['weight']+self.query(v, r)) <= self.delay_limit[s]:
                self.relevance[u][v].add(s)
                updated.add((u, v))
        for s in self.src2recv:
            for u, v in updated:
                if s in self.relevance[u][v]:
                    _sum, ok = self.check_bandwidth_limit(u, v)
                    # if ok:



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

    model = HeatDegreeModel(G, D, B, S2R)


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
    model = HeatDegreeModel(G, D, B, S2R)

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
        model.add_recv(S[0], r)

    #     relevance3 = relavence_matrix.relavence_matrix(G, distance, D, S2R)
    #     heat3 = heat_degree_matrix(relevance3, G, S, D, B)
    #
    # print(f"S: {S[0]}\tR: {S2R[S[0]]}\tr: {r}\toperation: {'add' if add else 'delete'}\n")
    #
    # for i in range(len(heat1)):
    #     for j in range(len(heat1[i])):
    #         if heat1[i][j] == inf: continue
    #         print(
    #             f"heat1[{i}][{j}]: {heat1[i][j]}\theat3[{i}][{j}]: {heat3[i][j]}\tdiff: {heat1[i][j] != heat3[i][j]}\n")


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
    print(model.routing_trees)
    # print(model.heat)


if __name__ == '__main__':
    test_model()
    # test_relevance_run_time()
    # test_member_change()
    # test_heat_matrix_based_routing()
