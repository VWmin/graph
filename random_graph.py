import networkx as nx
import matplotlib.pyplot as plt  # 导入 Matplotlib 工具包
import random
import numpy as np

def random_graph(n, p, w):
    G = nx.Graph()  # 创建无向图
    for u, v in nx.erdos_renyi_graph(n, p).edges():
        G.add_edge(u, v, weight=int(random.uniform(1, w)))
    return G

def print_graph(G, show_weight=True):
    pos = nx.spring_layout(G, iterations=20)  # 用 FR算法排列节点
    nx.draw(G, pos, with_labels=True, alpha=0.5)
    if show_weight:
        labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
    plt.show()  # 显示图形

def demo_graph():
    # G = nx.Graph()  # 创建无向图
    # G.add_edge(0, 1, weight=39)
    # G.add_edge(0, 2, weight=33)
    # G.add_edge(0, 3, weight=15)
    # G.add_edge(1, 3, weight=21)
    # G.add_edge(1, 6, weight=46)
    # G.add_edge(2, 4, weight=23)
    # G.add_edge(3, 4, weight=40)
    # G.add_edge(3, 5, weight=18)
    # G.add_edge(3, 6, weight=71)
    # G.add_edge(4, 7, weight=29)
    # G.add_edge(5, 7, weight=25)
    # G.add_edge(5, 8, weight=25)
    # G.add_edge(6, 8, weight=20)
    # G.add_edge(7, 8, weight=45)
    A = np.array([
        [0, 39, 33, 15, 0, 0, 0, 0, 0],
        [39, 0, 0, 21, 0, 0, 46, 0, 0],
        [33, 0, 0, 0, 23, 0, 0, 0, 0],
        [15, 21, 0, 0, 40, 18, 71, 0, 0],
        [0, 0, 23, 40, 0, 0, 0, 29, 0],
        [0, 0, 0, 18, 0, 0, 0, 25, 25],
        [0, 46, 0, 71, 0, 0, 0, 0, 20],
        [0, 0, 0, 0, 29, 25, 0, 0, 45],
        [0, 0, 0, 0, 0, 25, 20, 45, 0],
        ])
    G = nx.from_numpy_array(A)
    return G

def demo_graph_kmb():
    A = np.array([
        [0, 10, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 8, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 9, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0.5, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0.5],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        ])
    G = nx.from_numpy_array(A)
    return G