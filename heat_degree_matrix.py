import networkx as nx

def heatr_degree_matrix(relavence, G:nx.Graph):
    max_w = 0
    V = G.number_of_nodes()
    for u, v, w in G.edges.data('weight'):
        max_w = max(max_w, w)
    
    