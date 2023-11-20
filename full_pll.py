import networkx as nx

import dec_pll_weighted
import inc_pll_weighted
import pll_weighted


# 无向无权图全动态PLL算法
class FullPLL:
    def __init__(self, g: nx.Graph):
        self.g = g
        self.stamp = 0
        # init labels
        self.labels = pll_weighted.weighted_pll(self.g)
        self.cache = {}

    def __next_stamp__(self):
        self.stamp += 1
        self.cache = {}

    def query(self, u, v):
        if (u, v) not in self.cache:
            self.cache[(u, v)] = pll_weighted.query_distance(self.labels, u, v)
        return self.cache[(u, v)]

    # inc algorithm
    def add_edge(self, u, v, val):
        # 如果u v都不是已有的节点，无法增加边
        if not self.g.has_node(u) or not self.g.has_node(v):
            return
        # 如果u v已经有边，不需要增加
        if self.g.has_edge(u, v):
            return
        # 图版本自增
        self.__next_stamp__()
        # 增加边
        self.g.add_edge(u, v, weight=val)
        # 调用增量算法
        self.labels = inc_pll_weighted.inc_pll_w(self.g, self.labels, u, v)

    # dec algorithm
    def remove_edge(self, u, v):
        # 如果没有边，无法移除
        if not self.g.has_edge(u, v):
            return
        self.__next_stamp__()

        raw_val = self.g[u][v]['weight']
        self.g.remove_edge(u, v)

        self.labels = dec_pll_weighted.dec_pll_w(self.g, raw_val, u, v, self.labels)

    def change_edge_weight(self, u, v, new_val):
        # 不存在的边无法修改边权
        if not self.g.has_edge(u, v):
            return
        self.__next_stamp__()

        raw_val = self.g[u][v]['weight']
        self.g[u][v]['weight'] = new_val

        if new_val > raw_val:
            # dec alg
            self.labels = dec_pll_weighted.dec_pll_w(self.g, raw_val, u, v, self.labels)
        else:
            # inc alg
            self.labels = inc_pll_weighted.inc_pll_w(self.g, self.labels, u, v)

    # def kmb(self, terminals):
    #     import time
    #     # 1. get G1 complete graph with terminals
    #     t0 = time.time()
    #     dis = {}
    #     G1 = nx.Graph()
    #     for u in terminals:
    #         for v in terminals:
    #             if u == v:
    #                 continue
    #             G1.add_edge(u, v, weight=self.query(u, v))
    #
    #     t1 = time.time()
    #     print("G1 cost: ", t1 - t0)
    #
    #     # 2. prime G1
    #     T1E = nx.minimum_spanning_edges(G1, data=False)
    #     t2 = time.time()
    #     print("prime G1 cost: ", t2 - t1)
    #
    #     # 3. recover Gs
    #     Gs = nx.Graph()
    #     for edge in list(T1E):
    #         i, j = edge
    #         path = dis[i][j][1]
    #         for k in range(len(path) - 1):
    #             Gs.add_edge(path[k], path[k + 1], weight=G[path[k]][path[k + 1]]['weight'])
    #     t3 = time.time()
    #     print("recover Gs cost: ", t3 - t2)
    #
    #     # 4. prime Ts
    #     Ts = nx.minimum_spanning_tree(Gs)
    #     t4 = time.time()
    #     print("prime Ts cost: ", t4 - t3)
    #
    #     # 5. reserve terminals - remove any leaf that not in terminals
    #     # 5.1 collect leafs
    #     target = set(terminals)
    #     leafs = set()
    #     for node in Ts.nodes:
    #         if Ts.degree(node) == 1:
    #             leafs.add(node)
    #     leafs = leafs - target
    #     # 5.2 remove leaf and edge not related to terminals
    #     for node in leafs:
    #         # print("terminals: ", target, ", leafs: ", leafs,  ", checking node: ", node)
    #         next = node
    #         while next:
    #             neighbors = list(Ts.neighbors(next))
    #             Ts.remove_node(next)
    #             next = neighbors[0] if len(neighbors) == 1 else None
    #     t5 = time.time()
    #     print("reserve terminals cost: ", t5 - t4)
    #     return Ts

# FIXME 如果图不连通，算法有效吗？
