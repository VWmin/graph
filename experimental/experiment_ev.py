import socket
import pickle

import sys

sys.path.append('/home/fwy/Desktop/graph')
sys.path.append('/home/fwy/Desktop/graph/experimental')

from experiment_info import ExperimentInfo


def run_server(info: ExperimentInfo):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('127.0.0.1', 8888))
    server.listen(1)

    print("Server listening on port 8888...")

    while True:
        connection, address = server.accept()
        print("Connection from:", address)

        data = pickle.dumps(info)
        connection.sendall(data)

        connection.close()
    # server.close()


def acquire_info() -> ExperimentInfo:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 8888))
    data, buffer_size = b"", 4096
    while True:
        chunk = client.recv(buffer_size)
        if not chunk:
            break
        data += chunk
    # id starts from 0.
    info: ExperimentInfo = pickle.loads(data)
    client.close()
    return info


def send_ok():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('127.0.0.1', 8889))
    msg = "ok"
    msg_bytes = msg.encode('utf-8')
    client.sendall(msg_bytes)
    client.close()


if __name__ == "__main__":
    import random_graph

    g = random_graph.demo_graph()
    # g = random_graph.gt_itm_example()
    run_server(ExperimentInfo(g))
