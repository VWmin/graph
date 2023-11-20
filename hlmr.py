import itertools

import networkx as nx

import relavence_matrix
import util

from math import inf


def hlmr(g: nx.Graph, s2r, delay_limit, bandwidth_require):
    Ts = {}
    for s in s2r:
        Ts[s] = {}
        for r in s2r[s]:
            cost, path = hcp(g, s, r, bandwidth_require)
            if cost == inf:
                return Ts
            if cost > delay_limit[s]:
                # 计算s到其他节点的最短路
                # 计算其他节点到r的最短路
                rp, minc = None, inf
                n = len(path)
                for i in range(n):
                    for j in range(i + 1, n):
                        tmp_path = sp(g, path[0], path[i]) + trim(path, i, j) + sp(g, path[j], path[n - 1])
                        tmp_cost = d(g, tmp_path)
                        if tmp_cost <= delay_limit[s] and hd(g, tmp_path) < minc:
                            rp, minc = tmp_path, tmp_cost
                Ts[s][r] = rp
            else:
                Ts[s][r] = path

            # 更新剩余带宽
            for i in range(len(Ts[s][r]) - 1):
                u, v = Ts[s][r][i], Ts[s][r][i+1]
                g[u][v]['bandwidth'] -= bandwidth_require[s]
    return Ts


def d(g: nx.Graph, path):
    t = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        t += g[u][v]['weight']
    return t


def hd(g: nx.Graph, path):
    t = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        t += g[u][v]['heat']
    return t


def sp(g: nx.Graph, s, r):
    if s == r:
        return []
    cost, path = nx.single_source_dijkstra(g, s, r)
    return path


def trim(path, i, j):
    return path[i: j + 1]


def hcp(g: nx.Graph, s, r, bandwidth_require):
    # 忽略边：
    #   1. 现有的以s为根的多播树不包含这条边
    #   2. 此链路的剩余带宽不满足来自s的多播会话的带宽要求
    # return nx.single_source_dijkstra(g, s, r)
    paths = {s: [s]}
    dist = {}
    seen = {s: 0}
    c = itertools.count()
    pq = util.PriorityQueue()
    pq.push((0, next(c), s))
    while pq.size():
        d, _, v = pq.pop()
        if v in dist:
            continue
        dist[v] = d
        if v == r:
            break
        for u in g.neighbors(v):
            if g[v][u]['bandwidth'] < bandwidth_require[s]:
                continue
            cost = g[v][u]['weight']
            vu_dist = dist[v] + cost
            if u not in seen or vu_dist < seen[u]:
                seen[u] = vu_dist
                pq.push((vu_dist, next(c), u))
                paths[u] = paths[v] + [u]
    if r not in dist:
        return inf, None
    return dist[r], paths[r]



def test_hlmr():
    import random_graph

    g = random_graph.random_graph(100, 0.1, 100)
    relavence_matrix.add_random_bandwidth_attr(g, 100, 1, 1)
    s2r = {1: {5, 6, 7, 8, 9}}
    delay_limit = {1: 200}
    bandwidth_require = {1: 50}
    Ts = hlmr(g, s2r, delay_limit, bandwidth_require)
    print(Ts)


if __name__ == '__main__':
    test_hlmr()
    # path = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # print(path[1:3])
