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
import math
import threading
import time

import networkx as nx
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ether_types, arp, ethernet, ipv4, lldp
from ryu.topology import event, switches
from ryu.topology.api import get_link, get_all_link
from ryu.topology.switches import LLDPPacket

from ryu import utils
from ryu.lib import hub

import sys

import heat_degree_matrix

sys.path.append('/home/fwy/Desktop/graph')
sys.path.append('/home/fwy/Desktop/graph/experimental')
import util


class MULTIPATH_13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'switches': switches.Switches,
    }

    def __init__(self, *args, **kwargs):
        super(MULTIPATH_13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.arp_received = {}
        self.arp_port = {}
        self.datapaths = {}
        self.echo_delay = {}
        self.link_delay = {}
        # self.net = random_graph.demo_graph()
        self.network = nx.Graph()
        self.network.add_node(0)  # dummy node
        self.lock = threading.Lock()
        self.switch_service = lookup_service_brick("switches")
        self.monitor_thread = hub.spawn(self._monitor)
        self.experimental_thread = hub.spawn(self.run_experiment)

    @set_ev_cls(ofp_event.EventOFPErrorMsg,
                [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.error('OFPErrorMsg received: type=0x%02x code=0x%02x ', msg.type, msg.code)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
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
        self.logger.info("switch:%s connected", dpid)

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
        except ValueError as error:
            self.logger.warn("failed to get echo delay to dpid(%s), error: %s", dpid, error)

    def send_group_mod(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Hardcoding the stuff, as we already know the topology diagram.
        # Group table1
        # Receiver port2, forward it to port2 and Port3

        actions1 = [parser.OFPActionOutput(2)]
        actions2 = [parser.OFPActionOutput(3)]
        buckets = [parser.OFPBucket(actions=actions1),
                   parser.OFPBucket(actions=actions2)]
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD,
                                 ofproto.OFPGT_ALL, 50, buckets)
        datapath.send_msg(req)

    def _monitor(self):
        while True:
            hub.sleep(5)
            self.send_echo_request()
            self.lock.acquire()
            link_list = get_all_link(self)
            for link in link_list:
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
            self.lock.release()

    # def add_host(self, host_mac, inport, dpid):
    #     if host_mac not in self.network:
    #         print("add host into network:", host_mac)
    #
    #         self.network.add_node(host_mac, connected=dict())
    #         self.network.nodes[host_mac]['connected'][inport] = dpid
    #
    #         self.network.add_edge(host_mac, dpid, port=inport)
    #         self.network.add_edge(dpid, host_mac, port=inport)

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
            """
                     c0
                   a    b 
                 s1   c  s2
                 T1 = a+c+b; LLDP c0->s1->s2->c0
                 T2 = b+c+a; LLDP c0->s2->s1->c0
                 Ta = 2a;    echo c0->s1->c0
                 Tb = 2b;    echo c0->s2->c0
                 avg link delay s1-s2 = (T1+T2-Ta-Tb)/2 or T1-(Ta+Tb)/2 or T2-(Ta+Tb)/2
            """
            try:
                src_dpid, src_outport = LLDPPacket.lldp_parse(msg.data)
                dst_dpid, dst_inport = dpid, in_port
                for port in self.switch_service.ports:
                    if src_dpid == port.dpid and src_outport == port.port_no:
                        send_time = self.switch_service.ports[port].timestamp
                        if send_time is None:
                            return
                        t = time.time() - send_time
                        c = t - (self.echo_delay[src_dpid] + self.echo_delay[dst_dpid]) / 2
                        self.link_delay[(src_dpid, dst_dpid)] = c
                        self.logger.debug(f"link delay {src_dpid} <---> {dst_dpid} is {c}")
                        break
            except KeyError:
                return

        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            self.logger.debug("ARP processing")
            arp_pkt = pkt.get_protocol(arp.arp)
            # self.add_host(arp_pkt.src_mac, in_port, datapath.id)
            self.handle_arp(datapath, msg, arp_pkt, eth, in_port)

        elif eth.ethertype == ether_types.ETH_TYPE_IP:
            ip_pkt = pkt.get_protocol(ipv4.ipv4)
            self.logger.info("dpid=%s processing %s --> %s", dpid, ip_pkt.src, ip_pkt.dst)
            if dpid not in self.mac_to_port:
                self.logger.info("Dpid=%s is not in mac_to_port", dpid)
                return
            if eth.dst in self.mac_to_port[dpid]:
                # Normal flows
                out_port = self.mac_to_port[dpid][eth.dst]
                actions = [parser.OFPActionOutput(out_port)]
                # match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, in_port=in_port,
                #                         ipv4_src=ip_pkt.src, ipv4_dst=ip_pkt.dst)
                # self.add_flow(datapath, 1, match, actions)
                self.send_packet_out(datapath, msg, actions)
            elif ip_pkt.dst == '224.0.1.1':
                self.logger.debug("dpid=%s recv multicast req", datapath.id)

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

    def run_experiment(self):
        self.logger.info("enter experiment")
        hub.sleep(30)

        # datapath = self.datapaths[1]
        # parser = datapath.ofproto_parser
        # self.send_group_mod(datapath)
        # actions = [parser.OFPActionGroup(group_id=50)]
        # match = parser.OFPMatch(in_port=1)
        # self.add_flow(datapath, 10, match, actions)
        # self.logger.info("installed")

        b_lo, b_hi = 5e6 / 2, 10e6 / 2  # use half of the bandwidth for multicast
        b_req_lo, b_req_hi = 512 * 1e3, 1e6  # per multicast required
        d_lo, d_hi = 1, 10
        d_req_lo, d_req_hi = 50, 100

        # for edge in self.network.edges:
        #     print(self.network.edges[edge]['weight'])

        self.lock.acquire()
        util.add_attr_with_random_value(self.network, "bandwidth", int(b_lo), int(b_hi))
        util.add_attr_with_random_value(self.network, "weight", d_lo, d_hi)
        S = util.random_s_from_graph(self.network, 1)
        S2R = util.random_s2r_from_graph(self.network, 3, S)
        B = util.random_d_with_range(S, int(b_req_lo), int(b_req_hi))
        D = util.random_d_with_range(S, d_req_lo, d_req_hi)

        mine_instance = heat_degree_matrix.HeatDegreeModel(self.network, D, B, S2R)
        mine_instance.statistic()
        self.lock.release()

        group_no = 1
        for root in mine_instance.routing_trees:
            multicast_ip = f'224.0.1.{group_no}'
            group_no += 1
            tree = mine_instance.routing_trees[root]

            # install group table and flow entry for sw -> sw
            self.install_routing_tree(tree, root, S2R[root], multicast_ip)

            # log info
            graph_string = "\nDirected Graph:\n"
            for edge in tree.edges():
                graph_string += f"{edge[0]} -> {edge[1]};\n"
            self.logger.info(f"the routing tree of {root} is {graph_string}")
        self.logger.info(f"install group flow ok, s2r is {S2R}")

    def install_routing_tree(self, tree, root, recvs, multicast_ip):
        datapath = self.datapaths[root]

        succ = list(tree.successors(root))
        group_id = 50 + root

        if len(succ) > 0:
            self.logger.info("installing group table and flow to %s", root)
            out_ports = [self.network[root][e]['dpid_to_port'][e] for e in succ]
            if root in recvs:
                out_ports.append(1)
            self.send_group_mod_flood(datapath, out_ports, group_id)
            self.add_flow_to_group_table(datapath, group_id, multicast_ip)

            for node in succ:
                self.install_routing_tree(tree, node, recvs, multicast_ip)
        elif len(succ) == 0 and root in recvs:
            self.add_flow_to_connected_host(datapath, multicast_ip)

    @staticmethod
    def send_group_mod_flood(datapath, out_ports, group_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        buckets = [parser.OFPBucket(actions=[parser.OFPActionOutput(out_port)]) for out_port in out_ports]
        req = parser.OFPGroupMod(datapath, ofproto.OFPGC_ADD, ofproto.OFPGT_ALL, group_id, buckets)
        datapath.send_msg(req)

    def add_flow_to_group_table(self, datapath, group_id, multicast_ip):
        parser = datapath.ofproto_parser
        # match = parse.OFPMatch(in_port=port,eth_type=0x0800, ip_proto=6, ipv4_dst=server_ip, tcp_src=tcp_pkt.src_port)
        match = parser.OFPMatch(eth_type=0x800, ipv4_dst=multicast_ip)
        actions = [parser.OFPActionGroup(group_id=group_id)]
        self.add_flow(datapath, 1, match, actions)

    def add_flow_to_connected_host(self, datapath, multicast_ip):
        self.logger.info("installing sw to host flow to %s", datapath.id)
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_type=0x800, ipv4_dst=multicast_ip)
        actions = [parser.OFPActionOutput(1)]
        self.add_flow(datapath, 1, match, actions)
