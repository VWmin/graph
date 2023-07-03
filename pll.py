import networkx as nx
import random_graph
import time

inf = 1000000000

def naive_landmark_labeling(G:nx.Graph):
    """
    Naive landmark labeling algorithm
    :param G: networkx graph, undirected, unweighted
    :return: landmark label dictionary
    """
    # initialize landmark label dictionary
    landmark_label = dict()
    def bfs(G:nx.Graph, root):
        distance = {}

        que = []
        que.append(root)
        distance[root] = 0
        while que:
            u = que.pop(0)
            for v in G.neighbors(u):
                if v not in distance:
                    distance[v] = distance[u] + 1
                    que.append(v)

        return distance

    # go through each vertices in G
    for v in G.nodes:
        landmark_label[v] = bfs(G, v)
    
    return landmark_label

def pruned_landmark_labeling(G:nx.Graph):
    pass

def query_distance(labels, u, v):
    """
    Query distance between u and v using landmark labels
    :param labels: landmark label dictionary
    :param u: vertex u
    :param v: vertex v
    :return: distance between u and v
    """
    if u == v:
        return 0
    if u not in labels or v not in labels:
        return inf
    distance = inf
    for landmark in labels[u]:
        if landmark in labels[v]:
            distance = min(distance, labels[landmark][u] + labels[landmark][v])
    return distance


# t1 = time.time()
# G = random_graph.random_graph(10, 0.3, 100)
# lables = naive_landmark_labeling(G)
# t2 = time.time()
# print("naive_landmark_labeling: ", t2 - t1)

# d1 = query_distance(lables, 0, 8)
# print("d1: ", d1)

# d2 = nx.shortest_path_length(G, 0, 8)
# print("d2: ", d2)

# random_graph.print_graph(G)