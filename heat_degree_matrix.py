import networkx as nx

def heat_degree_matrix(relavence, G:nx.Graph, Ex, s, r):
    max_w = 0
    V = G.number_of_nodes()
    for u, v, w in G.edges.data('weight'):
        max_w = max(max_w, w)

    def heat_degree_matrix_ij(Ts, i, j):
        # 如果边ij是s的候选边，且已在以s为源的现存多播树中
        # or 边ij是s的候选边，但不在以r为源的现存多播树中，且边ij的带宽满足所有以其为候选边的源的带宽要求之和
        if s in relavence[i][j]:
            if G[i][j] in Ts or checkB():
                return 'case1'
            else:
                return 'case2'
        else :
            return 'case3'
    