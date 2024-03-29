import itertools
import time

import networkx as nx
import numpy as np

import heat_degree_matrix
import relavence_matrix
import util

from math import inf


class HLMR:
    def __init__(self, g: nx.Graph, delay_limit, bandwidth_require, s2r):
        self._g = g
        self._delay_limit = delay_limit
        self._bandwidth_require = bandwidth_require
        self._src2recv = s2r
        self.routing_trees = {}
        self.op_history = []
        self._heat_base = heat_degree_matrix.HeatDegreeBase(self._g, self._delay_limit, self._bandwidth_require,
                                                            self._src2recv, self.routing_trees, False)
        self._routing()

    def _routing(self):
        t = time.time()
        tmp_trees = {}
        for s in self._src2recv:
            tmp_trees[s] = {}
            for r in self._src2recv[s]:
                cost, path = self.hcp(s, r)
                if not path:
                    tmp_trees[s][r] = []
                    continue
                if cost > self._delay_limit[s]:
                    # 计算s到其他节点的最短路
                    # 计算其他节点到r的最短路
                    rp, minc = path, inf
                    n = len(path)
                    for i in range(n):
                        for j in range(i + 1, n):
                            tmp_path = self.sp(path[0], path[i]) + self.trim(path, i, j) + self.sp(path[j], path[n - 1])
                            tmp_cost = self.d(tmp_path)
                            if tmp_cost <= self._delay_limit[s] and self.hd(s, tmp_path) < minc:
                                rp, minc = tmp_path, tmp_cost
                    rp = remove_dup_element(rp)
                    tmp_trees[s][r] = rp
                else:
                    tmp_trees[s][r] = path
        self.op_history.append(("routing", time.time() - t))

        for s in self._src2recv:
            self.routing_trees[s] = nx.DiGraph()
            for r in self._src2recv[s]:
                path = tmp_trees[s][r]
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    self.routing_trees[s].add_edge(u, v)

    def hcp(self, s, r):
        paths = {s: [s]}
        dist = {}
        seen = {s: 0}
        c = itertools.count()
        pq = util.PriorityQueue()
        pq.push((0, next(c), s))
        while pq.size():
            _d, _, v = pq.pop()
            if v in dist:
                continue
            dist[v] = _d
            if v == r:
                break
            for u in self._g.neighbors(v):
                # _, ok = self._heat.check_bandwidth_limit(u, v)
                # if not ok:
                #     continue
                cost = self._heat_base.get_heat_degree_ij(s, u, v)
                vu_dist = dist[v] + cost
                if u not in seen or vu_dist < seen[u]:
                    seen[u] = vu_dist
                    pq.push((vu_dist, next(c), u))
                    paths[u] = paths[v] + [u]
        if r not in dist:
            return inf, None
        return dist[r], paths[r]

    def d(self, path):
        t = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if u == v:
                continue
            t += self._g[u][v]['weight']
        return t

    def hd(self, s, path):
        t = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if u == v:
                continue
            t += self._heat_base.get_heat_degree_ij(s, u, v)
        return t

    def sp(self, s, r):
        if s == r:
            return []
        cost, path = nx.single_source_dijkstra(self._g, s, r)
        return path

    @staticmethod
    def trim(path, i, j):
        return path[i: j + 1]

    def statistic(self):
        print("hlmr statistic info >>> ")
        self._heat_base.statistic()
        for op, t in self.op_history:
            print(f"operation: {op:<20} \t\t cost: {round(t, 4)}s")

    def init_time(self):
        return self._heat_base.init_time() + self.last_time()

    def last_time(self):
        return self.op_history[-1][1]


def remove_dup_element(arr: list):
    new_arr = []
    for e in arr:
        if e not in new_arr:
            new_arr.append(e)
    return new_arr


def test_hlmr():
    import random_graph

    g = random_graph.random_graph(100, 0.1, 100)
    relavence_matrix.add_random_bandwidth_attr(g, 100, 1, 1)
    s2r = {1: {5, 6, 7, 8, 9}}
    delay_limit = {1: 200}
    bandwidth_require = {1: 50}
    instance = HLMR(g, delay_limit, bandwidth_require, s2r)
    for tree in instance.routing_trees.values():
        random_graph.print_graph(tree)


if __name__ == '__main__':
    test_hlmr()
    # path = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # print(path[1:3])
