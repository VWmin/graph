
inf = 9999
def read_graph_from_file():
    with open('in.txt', 'r') as f:
        lines = f.readlines()
        n = int(lines[0])
        G = [[inf for j in range(n)] for i in range(n)]
        for i in range(1, len(lines)):
            line = lines[i].split()
            u = int(line[0])
            v = int(line[1])
            w = int(line[2])
            G[u][v] = w
            G[v][u] = w
    return G

def floyd(G):
    n = len(G)
    D = [[G[i][j] for j in range(n)] for i in range(n)]
    for i in range(n):
        D[i][i] = 0
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if D[i][k] + D[k][j] < D[i][j]:
                    D[i][j] = D[i][k] + D[k][j]
    return D


def gen_relavence(G, distance, D, S2R):
    n = len(G)
    # initialize relavence matrix
    relavence = [[set() for i in range(n)] for j in range(n)]
    # fill relavence matrix
    for i in range(n):
        for j in range(i+1, n):
            if G[i][j] != inf:
                for s in S2R:
                    R = S2R[s]
                    for r in R:
                        if distance[s][i] + G[i][j] + distance[j][r] <= D[s]:
                            relavence[i][j].add(s) 
    return relavence

def test_relavence():
    G = read_graph_from_file()
    distance = floyd(G)
    for i in range(len(G)):
        print(G[i])
    D = {
        0: 90,
        1: 90
    }
    S2R = {
        0: [4, 7],
        1: [8]
    }
    relavence = gen_relavence(G, distance, D, S2R)
    return relavence

# test_relavence()
