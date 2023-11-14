import networkx as nx
import time

import full_pll
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
        # 调用该类方法会修改图的结构
        self.__fpll__ = full_pll.FullPLL(self.g)
        self.__distance__ = 0
        self.__max_delay__ = max(dict(self.g.edges).items(), key=lambda x: x[1]['weight'])[1]['weight']
        self.__build_relevance__()
        self.__build_heat_matrix__()
        self.__routing__()

    def __build_relevance__(self):
        n = self.g.number_of_nodes()
        self.relevance = [[dict() for _ in range(n)] for _ in range(n)]

        for i, j in self.g.edges:
            i, j = (j, i) if i > j else (i, j)
            for s in self.src2recv:
                for r in self.src2recv[s]:
                    estimated = self.__get_estimate__(s, r, i, j)
                    if estimated <= self.delay_limit[s]:
                        self.__inc_relevance__(s, i, j)

    def __get_estimate__(self, s, r, i, j):
        if s == i or s == j:
            return self.g[i][j]['weight'] + min(self.query(i, r), self.query(j, r))
        elif r == i or r == j:
            return self.g[i][j]['weight'] + min(self.query(i, s), self.query(j, s))
        else:
            return self.query(s, i) + self.g[i][j]['weight'] + self.query(j, r)

    def __inc_relevance__(self, s, i, j):
        if s not in self.relevance[i][j]:
            self.relevance[i][j][s] = 1
        else:
            self.relevance[i][j][s] = self.relevance[i][j][s] + 1

    def __dec_relevance__(self, s, i, j):
        if s not in self.relevance[i][j]:
            return
        self.relevance[i][j][s] = self.relevance[i][j][s] - 1

    def __build_heat_matrix__(self):
        n = self.g.number_of_nodes()
        self.heat = [[self.__update_heat_degree_ij__(i, j) for j in range(n)] for i in range(n)]

    def __update_heat_degree_ij__(self, i, j):
        if not self.g.has_edge(i, j):
            return inf, inf, True
        _sum, available = self.check_bandwidth_limit(i, j)
        a = self.g[i][j]['weight'] / (self.g.number_of_nodes() * self.__max_delay__)
        b = pow(_sum / self.g[i][j]['bandwidth'], 2)
        return a, b, available

    def get_heat_degree_ij(self, s, i, j):
        i, j = (i, j) if i < j else (j, i)
        # 如果边ij是s的候选边，且已在以s为源的现存多播树中
        # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
        if s in self.relevance[i][j]:
            in_routing_tree = self.__is_routing_contains_edge__(s, i, j)
            edge_available = self.heat[i][j][2]
            if in_routing_tree or edge_available:
                return self.heat[i][j][0]
            else:
                return self.heat[i][j][1]
        else:
            return inf

    def __routing__(self):
        for s in self.src2recv:
            self.routing_trees[s] = {}
            for r in self.src2recv[s]:
                self.__single_source_routing__(s, r)

    def __single_source_routing__(self, s, r):
        _, path = nx.single_source_dijkstra(self.g, s, target=r,
                                            weight=lambda u, v, d: self.get_heat_degree_ij(s, u, v))
        self.routing_trees[s][r] = path

    def __pll_query__(self, u, v):
        return self.__fpll__.query(u, v)

    def __distance_query(self, u, v):
        if self.__distance__ == 0:
            self.__distance__ = nx.floyd_warshall_numpy(self.g)
        return self.__distance__[u][v]

    def __is_routing_contains_edge__(self, s, u, v) -> bool:
        if s not in self.routing_trees:
            return False
        for recv in self.routing_trees[s]:
            path = self.routing_trees[s][recv]
            for i in range(1, len(path)):
                a, b = path[i - 1], path[i]
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

    def print_heat_graph(self, s):
        labels = {}
        for u, v in self.g.edges:
            labels[u, v] = round(self.get_heat_degree_ij(s, u, v), 2)
        random_graph.print_graph_with_labels(self.g, labels)

    def add_recv(self, s, r):
        self.src2recv[s].append(r)
        updated = set()
        for u, v in self.g.edges:
            u, v = (v, u) if u > v else (u, v)
            estimated = self.__get_estimate__(s, r, u, v)
            if estimated <= self.delay_limit[s]:
                self.__inc_relevance__(s, u, v)
                updated.add((u, v))
        need_refactor = set()
        for u, v in updated:
            self.heat[u][v] = self.__update_heat_degree_ij__(u, v)
            for may_congested in self.src2recv:
                if not self.heat[u][v][2] and self.__is_routing_contains_edge__(may_congested, u, v):
                    need_refactor.add(may_congested)
        for to_refactor_s in need_refactor:
            self.routing_trees[to_refactor_s] = {}
            for to_refactor_r in self.src2recv[to_refactor_s]:
                self.__single_source_routing__(to_refactor_s, to_refactor_r)
        self.__single_source_routing__(s, r)

    def remove_recv(self, s, r):
        if s not in self.src2recv or r not in self.src2recv[s]:
            return
        self.src2recv[s].remove(r)
        del self.routing_trees[s][r]
        updated = set()
        for u, v in self.g.edges:
            u, v = (v, u) if u > v else (u, v)
            estimated = self.__get_estimate__(s, r, u, v)
            if estimated <= self.delay_limit[s]:
                self.__dec_relevance__(s, u, v)
                if self.relevance[u][v] == 0:
                    updated.add((u, v))
        for u, v in updated:
            self.heat[u][v] = self.__update_heat_degree_ij__(u, v)

    def change_delay(self, a, b, new_val):
        if not self.g.has_edge(a, b):
            return
        raw_val = self.g[a][b]['weight']
        self.__fpll__.change_edge_weight(a, b, new_val)
        if new_val < raw_val:
            # 延迟减少，原多播树依然满足
            return

        # 原本满足更新后不满足的侯选边集合
        updated = {}

        # 查看之前作为候选边的边，是否在修改后仍是侯选边
        for u, v in self.g.edges:
            u, v = (v, u) if v < u else u, v
            if len(self.relevance[u][v]) != 0:
                for s in list(self.relevance[u][v].keys()):
                    self.relevance[u][v][s] = 0
                    for r in self.src2recv[s]:
                        estimated = self.__get_estimate__(s, r, u, v)
                        if estimated <= self.delay_limit[s]:
                            self.__inc_relevance__(s, u, v)
                    if self.relevance[u][v][s] == 0:
                        updated[u, v] = updated.get((u, v), [])
                        updated[u, v].append(s)
                        del self.relevance[u][v][s]

        # 需要重建多播树的源节点集合
        need_refactor = set()

        # 如果(u, v)曾在s的多播树中，且现在可能拥塞或是不再作为侯选边，那么需要重构以s为源的多播树
        for u, v in updated:
            self.heat[u][v] = self.__update_heat_degree_ij__(u, v)
            for s in updated[u, v]:
                if ((not self.heat[u][v][2] or s not in self.relevance[u][v])
                        and self.__is_routing_contains_edge__(s, u, v)):
                    need_refactor.add(s)

        for to_refactor_s in need_refactor:
            self.routing_trees[to_refactor_s] = {}
            for to_refactor_r in self.src2recv[to_refactor_s]:
                self.__single_source_routing__(to_refactor_s, to_refactor_r)


def print_2d_array(array):
    for d1 in array:
        print(f"{d1}")
    print()


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
    print(model.routing_trees)

    import random
    add = random.randint(0, 1)
    print(add)
    if add == 1:
        r = random.randint(0, number_of_nodes - 1)
        while r in S2R[S[0]] or r == S[0]:
            r = random.randint(0, number_of_nodes - 1)
        model.add_recv(S[0], r)
        print(model.routing_trees)
    else:
        r = random.randint(0, number_of_nodes - 1)
        while r not in S2R[S[0]]:
            r = random.randint(0, number_of_nodes - 1)
        model.remove_recv(S[0], r)
        print(model.routing_trees)

    print(f"{model.src2recv}\tr: {r}\toperation: {'add' if add else 'delete'}\n")


def test_edge_change():
    weight_range = 100
    prob_of_recv = 0.2
    bandwidth_range = 100
    g = random_graph.demo_graph()
    number_of_nodes = g.number_of_nodes()
    # S = relavence_matrix.random_single_s(number_of_nodes)
    S = {2}
    relavence_matrix.add_random_bandwidth_attr(g, bandwidth_range, .5, .5)
    # S2R = relavence_matrix.random_S2R(number_of_nodes, S, prob_of_recv)
    S2R = {2: {7}}
    # D = relavence_matrix.random_D(S, weight_range)  # Delay limit of each source
    D = {2: 100}
    B = relavence_matrix.random_B(S, bandwidth_range, .4, .4)  # Bandwidth requirement of each source
    print(D)

    model = HeatDegreeModel(g, D, B, S2R)
    model.print_heat_graph(2)
    print_2d_array(model.relevance)
    print(model.routing_trees)
    model.change_delay(2, 4, 200)
    print(model.routing_trees)
    model.print_heat_graph(2)
    print_2d_array(model.relevance)


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
    # print(G[0][0])
    # random_graph.print_graph(G)


if __name__ == '__main__':
    # test_model()
    # test_relevance_run_time()
    # test_member_change()
    # test_heat_matrix_based_routing()
    test_edge_change()
