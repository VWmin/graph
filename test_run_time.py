import time
import random_graph
import relavence_matrix
import networkx as nx

def test_relaven_floyd_run_time():
    n, p, w = 50, 0.3, 100
    G = random_graph.random_graph(n, p, w)
    t1 = time.time()
    distance1 = nx.floyd_warshall_numpy(G)
    t2 = time.time()
    distance2 = relavence_matrix.general_floyd(G)
    t3 = time.time()

    print('floyd1 cost time: ', t2 - t1)
    print('floyd2 cost time: ', t3 - t2)
    

def test_relaven_run_time():
    n, p, w = 20, 0.3, 100
    G = random_graph.random_graph(n, p, w)
    S2R = relavence_matrix.random_S2R(n, relavence_matrix.random_S(n, 0.1), 0.2)
    D = relavence_matrix.random_D(S2R.keys(), w)

    t3 = time.time()
    distance1 = relavence_matrix.general_floyd(G)
    relavence1 = relavence_matrix.relavence_matrix(G, distance1, D, S2R)
    t4 = time.time()
    relavence2 = relavence_matrix.improved_relavence_matrix(G, D, S2R)
    t5 = time.time()

    print('relavence1 cost time: ', t4 - t3)
    print('relavence2 cost time: ', t5 - t4)
    print(relavence1 == relavence2)


def relavence_matrix_demo():
    G = random_graph.demo_graph()
    distance = nx.floyd_warshall_numpy(G)
    D = {
        0: 90,
        1: 90
    }
    S2R = {
        0: [4, 7],
        1: [8]
    }
    relavence1 = relavence_matrix.relavence_matrix(G, distance, D, S2R)
    relavence2 = relavence_matrix.improved_relavence_matrix(G, D, S2R)
    print(relavence1 == relavence2)

def all_simple_path_demo():
    G = random_graph.demo_graph()
    paths = relavence_matrix.all_simple_paths_cutoff_weight(G, 0, {4, 7}, 90)
    # paths = relavence_matrix.dfs(G, 0, 7, 90)
    for path in paths:
        print(path)

# nx.all_simple_paths()
# all_simple_path_demo()
# relavence_matrix_demo()
test_relaven_run_time()



