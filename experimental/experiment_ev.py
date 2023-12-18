import socket
import pickle
import networkx as nx

import random_graph


def run_server(graph: nx.Graph):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 8888))
    server.listen(1)

    print("Server listening on port 8888...")

    while True:
        connection, address = server.accept()
        print("Connection from:", address)

        data = pickle.dumps(graph)
        connection.sendall(data)

        connection.close()
    # server.close()


if __name__ == "__main__":
    graph = random_graph.demo_graph()
    print(graph)
    run_server(graph)
