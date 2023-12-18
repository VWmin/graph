import socket
import pickle
import networkx as nx



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


def acquire_graph():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 8888))
    data, buffer_size = b"", 4096
    while True:
        chunk = client.recv(buffer_size)
        if not chunk:
            break
        data += chunk
    # id starts from 0.
    graph = pickle.loads(data)
    client.close()
    return graph


if __name__ == "__main__":
    import random_graph
    run_server(random_graph.demo_graph())
