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

    def __next_stamp__(self):
        self.stamp += 1

    def query(self, u, v):
        return pll_weighted.query_distance(self.labels, u, v)

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

# FIXME 如果图不连通，算法有效吗？
