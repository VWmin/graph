# Copyright (C) 2016 Li Cheng BUPT www.muzixing.com.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import copy
import json
import pickle
import random
import subprocess
import threading
import time

import networkx as nx
import requests
from ryu import utils, cfg
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.lib.packet import packet, ether_types, arp, ethernet, ipv4, lldp
from ryu.topology import switches, event

from ryu.lib import hub

import heat_degree_matrix
import hlmr


def _get_exp_info():
    response = requests.get("http://localhost:8000/exp_info")
    return pickle.loads(response.content)


def _start_exp():
    requests.get("http://localhost:8001/exec")


class MULTIPATH_13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'switches': switches.Switches,
    }
    CONF = cfg.CONF

    def __init__(self, *args, **kwargs):
        super(MULTIPATH_13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.arp_received = {}
        self.arp_port = {}
        self.datapaths = {}
        self.echo_delay = {}
        self.link_delay = {}
        self.experiment_info = _get_exp_info()
        self.network = self.experiment_info.graph
        self.network.add_node(0)  # dummy node
        self.lock = threading.Lock()
        self.switch_service = lookup_service_brick("switches")
        self.monitor_thread = hub.spawn(self._monitor)
        # self.echo_thread = hub.spawn(self.run_echo)  # deprecated
        self.experimental_thread = hub.spawn(self.run_experiment)
        self.link_flag = False

    @set_ev_cls(ofp_event.EventOFPErrorMsg, [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.error('OFPErrorMsg received: type=0x%02x code=0x%02x message=%s',
                          msg.type, msg.code, utils.hex_array(msg.data))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 0, match, actions)

    def run_echo(self):
        while True:
            hub.sleep(10)
            connected_sw = len(self.datapaths)
            # not prepared.
            if connected_sw != self.network.number_of_nodes() - 1:
                self.logger.info(f"not prepared, connected sw: {connected_sw}")
                continue
            # already collected.
            if connected_sw == 0 or len(self.echo_delay) == connected_sw:
                continue
            self.logger.info("sending echo request to switches...")
            self.send_echo_request()

    def send_echo_request(self):
        for _, datapath in self.datapaths.items():
            parser = datapath.ofproto_parser
            echo = parser.OFPEchoRequest(datapath, data=bytes("%.12f" % time.time(), encoding="utf-8"))
            datapath.send_msg(echo)
            # interval 0.5s between datapaths
            hub.sleep(0.5)

    @set_ev_cls(ofp_event.EventOFPEchoReply, [MAIN_DISPATCHER, CONFIG_DISPATCHER, HANDSHAKE_DISPATCHER])
    def echo_reply_handler(self, ev):
        now_time = time.time()
        dpid = ev.msg.datapath.id
        try:
            echo_delay = now_time - eval(ev.msg.data)
            # save datapath delay
            self.echo_delay[dpid] = echo_delay
            self.logger.debug("controller to dpid(%s) echo delay is %s", dpid, echo_delay)
            if len(self.datapaths) != 0 and len(self.datapaths) == len(self.echo_delay):
                self.logger.info("got all echo reply")
        except ValueError as error:
            self.logger.warn("failed to get echo delay to dpid(%s), error: %s", dpid, error)

    def _monitor(self):
        while len(self.switch_service.link_delay) != len(self.network.edges):
            hub.sleep(10)
            self.logger.info(f"query links, expect {len(self.network.edges)}, "
                             f"now {len(self.switch_service.link_delay)}")
            self.lock.acquire()
            for link, delay in self.switch_service.link_delay.items():
                edge_key = (link.src.dpid, link.dst.dpid)
                if link.dst.dpid < link.src.dpid:
                    edge_key = (link.dst.dpid, link.src.dpid)

                # record dpid to port
                if 'dpid_to_port' not in self.network.edges[edge_key]:
                    self.network.edges[edge_key]['dpid_to_port'] = {
                        link.src.dpid: link.dst.port_no,
                        link.dst.dpid: link.src.port_no,
                    }

                # record delay time
                if edge_key not in self.link_delay:
                    self.link_delay[edge_key] = delay
                    self.network.edges[edge_key]['weight'] = delay

            self.lock.release()
        self.link_flag = True
        self.logger.info("monitor exit...")

    def construct_network_by_link(self, link):
        u, v = link.src, link.dst
        # check node
        if not self.network.has_node(u.dpid):
            self.network.add_node(u.dpid, port_to_dpid={}, dpid_to_port={})
        if not self.network.has_node(v.dpid):
            self.network.add_node(v.dpid, port_to_dpid={}, dpid_to_port={})
        # check edge
        if not self.network.has_edge(u.dpid, v.dpid):
            self.network.add_edge(u.dpid, v.dpid, dpid_to_port={
                u.dpid: v.port_no,
                v.dpid: u.port_no
            })
            # sw port -> connected sw dpid
            self.network.nodes[u.dpid]['port_to_dpid'][u.port_no] = v.dpid
            self.network.nodes[v.dpid]['port_to_dpid'][v.port_no] = u.dpid
        else:
            if len(self.link_delay) > 0:
                link = (u.dpid, v.dpid)
                delay = self.link_delay.get(link, -1)
                if delay <= 0:
                    delay = sum(self.link_delay.values()) / len(self.link_delay)
                self.network.edges[link]["weight"] = delay

    def add_host(self, host_mac, inport, dpid):
        if host_mac not in self.network:
            print("add host into network:", host_mac)

            self.network.add_node(host_mac, connected=dict())
            self.network.nodes[host_mac]['connected'][inport] = dpid

            self.network.add_edge(host_mac, dpid, port=inport)
            self.network.add_edge(dpid, host_mac, port=inport)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def send_packet_out(self, datapath, msg, actions):
        data = msg.data if msg.buffer_id == datapath.ofproto.OFP_NO_BUFFER else None
        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                                   in_port=msg.match['in_port'], actions=actions, data=data)
        datapath.send_msg(out)

    def arp_flow_and_forward(self, datapath, msg, in_port, out_port, eth_pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(out_port)]

        # if out_port != ofproto.OFPP_FLOOD:
        #     match = parser.OFPMatch(in_port=in_port, eth_dst=eth_pkt.dst, eth_type=eth_pkt.ethertype)
        #     if msg.buffer_id == ofproto.OFP_NO_BUFFER:
        #         self.add_flow(datapath, 1, match, actions)
        #     else:
        #         self.add_flow(datapath, 1, match, actions, msg.buffer_id)
        #         return
        self.send_packet_out(datapath, msg, actions)

    def handle_arp(self, datapath, msg, arp_pkt, eth_pkt, in_port):
        dpid = datapath.id
        ofproto = datapath.ofproto
        arp_key = (dpid, arp_pkt.src_mac, arp_pkt.dst_ip)

        self.arp_received.setdefault(arp_key, False)
        if not self.arp_received[arp_key]:
            self.arp_received[arp_key] = True
            self.arp_port[arp_key] = in_port
        elif self.arp_received[arp_key] and self.arp_port[arp_key] != in_port:
            return

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][arp_pkt.src_mac] = in_port
        out_port = self.mac_to_port[dpid].get(arp_pkt.dst_mac, ofproto.OFPP_FLOOD)

        self.arp_flow_and_forward(datapath, msg, in_port, out_port, eth_pkt)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes", ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            return
        elif eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.logger.debug("ARP processing")
            arp_pkt = pkt.get_protocol(arp.arp)
            # self.add_host(arp_pkt.src_mac, in_port, datapath.id)
            self.handle_arp(datapath, msg, arp_pkt, eth, in_port)

        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            # ip_pkt = pkt.get_protocol(ipv4.ipv4)
            # self.logger.info("dpid=%s processing %s --> %s", dpid, ip_pkt.src, ip_pkt.dst)
            if dpid not in self.mac_to_port:
                # self.logger.info("Dpid=%s is not in mac_to_port", dpid)
                return
            if eth.dst in self.mac_to_port[dpid]:
                # Normal flows
                out_port = self.mac_to_port[dpid][eth.dst]
                actions = [parser.OFPActionOutput(out_port)]
                # match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, in_port=in_port,
                #                         ipv4_src=ip_pkt.src, ipv4_dst=ip_pkt.dst)
                # self.add_flow(datapath, 1, match, actions)
                self.send_packet_out(datapath, msg, actions)

    def shortest_path_forward(self, datapath, msg, dst_dpid):
        """
        forwarding msg to single host by stp.
        :param datapath: current sw
        :param msg: msg to forward
        :param dst_dpid: dst sw
        """
        dpid = datapath.id
        parser = datapath.ofp_parser
        path = nx.shortest_path(self.network, dpid, dst_dpid)
        if len(path) == 1 and path[0] == dpid:
            self.logger.debug("arrived at %s", dpid)
            actions = [parser.OFPActionOutput(1)]
            self.send_packet_out(datapath, msg, actions)
        elif len(path) > 1:
            next_node = path[1]
            if self.network.has_edge(dpid, next_node):
                self.logger.debug("next to %s", next_node)
                out_port = self.network[dpid][next_node]['dpid_to_port'][next_node]
                self.logger.debug("out port is %s", out_port)
                actions = [parser.OFPActionOutput(out_port)]
                self.send_packet_out(datapath, msg, actions)

    def clear_flow_and_group_entries(self, dpid, gpid):
        # self.show_flow_entries(dpid)
        dp = self.datapaths[dpid]
        ofp = dp.ofproto
        parser = dp.ofproto_parser

        # 构建删除流表项的请求
        match = parser.OFPMatch()
        mod = parser.OFPFlowMod(
            datapath=dp,
            command=ofp.OFPFC_DELETE,
            out_port=ofp.OFPP_ANY,
            out_group=ofp.OFPG_ANY,
            priority=0,
            match=match,
            instructions=[]
        )
        dp.send_msg(mod)

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofp.OFPP_CONTROLLER)]
        self.add_flow(dp, 0, match, actions)

        # 构建组表项删除请求
        group_id = gpid
        req = parser.OFPGroupMod(dp, command=ofp.OFPGC_DELETE, type_=ofp.OFPGT_ALL, group_id=group_id, buckets=[])
        dp.send_msg(req)

        # print(f"cleared flow & group entries for dpid={dpid}")
        # self.show_flow_entries(dpid)

    def run_experiment(self):
        hub.sleep(30)
        self.logger.info(f"enter experiment at {time.time()}")
        while not self.link_flag:
            hub.sleep(10)

        self.logger.info(f"start experiment at {time.time()}")

        self.lock.acquire()

        net_cp = copy.deepcopy(self.network)
        instance1 = heat_degree_matrix.HeatDegreeModel(net_cp, self.experiment_info.D, self.experiment_info.B, self.experiment_info.S2R)
        # instance2 = hlmr.HLMR(net_cp, self.experiment_info.D, self.experiment_info.B, self.experiment_info.S2R)
        # instance3 = STPInstance(net_cp, self.experiment_info.D,  self.experiment_info.S2R)
        self.lock.release()

        self.install_routing_trees(instance1.routing_trees, self.experiment_info.S2R)

        self.logger.info(f"install group flow ok, s2r is {self.experiment_info.S2R}")
        hub.sleep(30)

        # _start_exp()
        self.logger.info("send ok to start script.")

        self.change_by_time("mine", heat_degree_matrix.HeatDegreeModel, instance1)

    def show_flow_entries(self, dpid):
        cmd = f"ovs-ofctl dump-flows s{dpid}"
        print(f"{cmd} >>>")
        subprocess.run(cmd, shell=True)

    def show_group_entries(self, dpid):
        cmd = f"ovs-ofctl dump-groups s{dpid}"
        print(f"{cmd} >>>")
        subprocess.run(cmd, shell=True)

    def change_by_time(self, name, method, pre_instance):
        random.seed(42)
        s = list(self.experiment_info.S)[0]
        nx.write_graphml(pre_instance.routing_trees[s], f"change/{name}-{0}.graphml")
        self.save_entries(name, pre_instance.routing_trees[s], 0)
        self.clear_entries(pre_instance.routing_trees)
        hub.sleep(15)
        for i in range(1, 11):
            print(f"turn {i} >>> ")
            now_instance = self.change_once(pre_instance, method)
            self.install_routing_trees(now_instance.routing_trees, self.experiment_info.S2R)
            hub.sleep(15)
            # prepare for next turn
            pre_instance = now_instance
            nx.write_graphml(pre_instance.routing_trees[s], f"change/{name}-{i}.graphml")
            self.save_entries(name, pre_instance.routing_trees[s], i)
            self.clear_entries(pre_instance.routing_trees)
        print("change by time finished.")

    def change_once(self, pre_instance, method):
        op = random.randint(1, 4)
        if op == 1:
            self.experiment_info.add_random_r()
        elif op == 2:
            self.experiment_info.remove_random_r()
        elif op == 3:
            src = random.choice(list(pre_instance.routing_trees.keys()))
            u, v = random.choice(list(pre_instance.routing_trees[src].edges))
            self.experiment_info.inc_link_delay(u, v)
        else:
            src = random.choice(list(pre_instance.routing_trees.keys()))
            tree = pre_instance.routing_trees[src]
            u, v = random.choice(list(tree.edges))
            netcp = copy.deepcopy(self.experiment_info.graph)
            netcp.remove_node(0)
            netcp.remove_edge(u, v)
            while not nx.is_connected(netcp):
                netcp.add_edge(u, v)
                u, v = random.choice(list(tree.edges))
                netcp.remove_edge(u, v)

            self.experiment_info.disable_link(u, v)
        instance = method(self.experiment_info.graph, self.experiment_info.D,
                          self.experiment_info.B, self.experiment_info.S2R)
        return instance

    def clear_entries(self, routing_trees):
        for src, tree in routing_trees.items():
            gpid = self.experiment_info.src_to_group_no[src]
            for n in tree.nodes:
                self.clear_flow_and_group_entries(n, gpid)

    def save_entries(self, name, tree, turn):
        content = ""
        for n in tree.nodes:
            command = f"ovs-ofctl dump-flows s{n}"
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            content += command + "\n"
            content += result.stdout + "\n"

            command = f"ovs-ofctl dump-groups s{n}"
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            content += command + "\n"
            content += result.stdout + "\n"

        with open(f"change/{name}-{turn}.txt", "w") as file:
            file.write(content)

    def check_heat(self, name, instance):
        print(f"{name} >>> ")
        for s in self.experiment_info.S2R:
            g = instance._heat_base.heat_graph(s)
            heat = {(u, v): round(g[u][v]['weight'], 3) for u, v in g.edges}
            # heat = instance._heat_base.heat
            #     heat = instance._heat_base.get_heat_degree_ij(s, i, j)
            print(f"{s} heat: {heat}")

    def check(self, name, instance):
        routing_trees = instance.routing_trees
        total_bw, total_delay, total_heat = 0, 0, 0
        for root, tree in routing_trees.items():
            tree_bw, tree_delay, tree_heat = 0, 0, 0
            for u, v in tree.edges:
                tree_bw += self.network[u][v]['bandwidth']
                tree_delay += self.network[u][v]['weight']
                tree_heat += instance._heat_base.get_heat_degree_ij(root, u, v)
            print(f"{name} root={root}, tree bw={tree_bw}, tree delay={tree_delay}, tree heat={tree_heat}")
            total_bw += tree_bw
            total_delay += tree_delay
            total_heat += tree_heat
        print(f"{name} total tree bw={total_bw}, tree delay={total_delay}, tree heat={total_heat}")

    def install_routing_trees(self, trees, S2R):
        output = {}
        for src in trees:
            group_id = self.experiment_info.src_to_group_no[src]
            multicast_ip = self.experiment_info.src_to_group_ip(src)
            tree = trees[src]

            # install group table and flow entry for sw -> sw
            self.install_routing_tree(tree, src, S2R[src], group_id, multicast_ip)

            # log info
            graph_string = "\nDirected Graph:\n"
            output[src] = []
            for edge in tree.edges():
                graph_string += f"{edge[0]} -> {edge[1]};\n"
                output[src].append(f"{edge[0]}-{edge[1]}")
            # self.logger.info(f"the routing tree of {src} is {graph_string}")

        # dump routing trees to file.
        with open('routing_trees.json', 'w') as json_file:
            json.dump(output, json_file, indent=4)

    def install_routing_tree(self, tree, cur_node, recvs, group_id, multicast_ip):
        datapath = self.datapaths[cur_node]

        succ = list(tree.successors(cur_node))

        if len(succ) > 0:
            # self.logger.info("installing group table and flow to %s", cur_node)
            out_ports = [self.network[cur_node][e]['dpid_to_port'][e] for e in succ]
            if cur_node in recvs:
                out_ports.append(1)
            self.send_group_mod_flood(datapath, out_ports, group_id)
            self.add_flow_to_group_table(datapath, group_id, multicast_ip)

            for node in succ:
                self.install_routing_tree(tree, node, recvs, group_id, multicast_ip)
        elif len(succ) == 0 and cur_node in recvs:
            self.add_flow_to_connected_host(datapath, multicast_ip)

    def send_group_mod_flood(self, datapath, out_ports, group_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        buckets = [parser.OFPBucket(actions=[parser.OFPActionOutput(out_port)]) for out_port in out_ports]
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD, ofproto.OFPGT_ALL, group_id, buckets)
        datapath.send_msg(req)
        # self.dp_to_group_mod.setdefault(datapath.id, [])
        # self.dp_to_group_mod[datapath.id].append(req)

    def add_flow_to_group_table(self, datapath, group_id, multicast_ip):
        parser = datapath.ofproto_parser
        # match = parse.OFPMatch(in_port=port,eth_type=0x0800, ip_proto=6, ipv4_dst=server_ip, tcp_src=tcp_pkt.src_port)
        match = parser.OFPMatch(eth_type=0x800, ipv4_dst=multicast_ip)
        actions = [parser.OFPActionGroup(group_id=group_id)]
        self.add_flow(datapath, 1, match, actions)
        # self.dp_to_flow_mod.setdefault(datapath.id, [])
        # self.dp_to_flow_mod[datapath.id].append(actions)

    def add_flow_to_connected_host(self, datapath, multicast_ip):
        # self.logger.info("installing sw to host flow to %s", datapath.id)
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=0x800, ipv4_dst=multicast_ip)
        actions = [parser.OFPActionOutput(1)]
        self.add_flow(datapath, 1, match, actions)


class STPInstance:
    def __init__(self, g: nx.Graph, delay_limit, s2r):
        self._g = g
        self._delay_limit = delay_limit
        self._src2recv = s2r

        self.routing_trees = {}
        self.op_histories = []

        self.routing()

    def routing(self):
        t = time.time()
        trees = {}
        for s in self._src2recv:
            trees[s] = {}
            self.routing_trees[s] = nx.DiGraph()
            for r in self._src2recv[s]:
                cost, path = nx.single_source_dijkstra(self._g, s, r)
                if not path or cost > self._delay_limit[s]:
                    trees[s][r] = []
                    continue
                for i in range(len(path) - 1):
                    self.routing_trees[s].add_edge(path[i], path[i + 1])

        self.op_histories.append(("routing", time.time() - t))
