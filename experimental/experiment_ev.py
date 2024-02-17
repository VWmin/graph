import socket
import pickle

import cherrypy
import zerorpc
import sys

import random_graph

sys.path.append('/home/fwy/Desktop/graph')
sys.path.append('/home/fwy/Desktop/graph/experimental')

from experiment_info import ExperimentInfo


class ExpInfoServer:
    def __init__(self, info):
        self.info = info

    @cherrypy.expose
    def exp_info(self):
        return pickle.dumps(self.info)


if __name__ == "__main__":
    # graph = random_graph.demo_graph()
    graph = random_graph.gt_itm_ts(325)
    expinfo = ExperimentInfo(graph)

    cherrypy.config.update({'server.socket_port': 8000})
    cherrypy.quickstart(ExpInfoServer(expinfo))
