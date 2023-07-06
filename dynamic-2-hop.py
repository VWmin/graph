import networkx as nx
import random_graph
import time

inf = 1000000000

def WPSL(G:nx.Graph):
    L = []
    L.append( {v:{v:0} for v in G.nodes} )
    h = 1
    while L[h-1]:
        for v in G.nodes:
            cand = set()
            for u in G.neighbors(v):
                cand.add(L[u].keys())
            for w in cand:
                if G.degree(w) < G.degree(v) or Q(w, v, L, h) <= G[v][u]['weight']+L[h-1][u][w]:
                    continue
                L[h][v][w] = G[v][u]['weight']+L[h-1][u][w]
        h = h+1
    return L

def Q(u, v, L, h):
    for i in range(h):
        pass