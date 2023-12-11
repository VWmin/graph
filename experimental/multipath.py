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

import networkx as nx
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER, HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ether_types, arp, ethernet, ipv4
from ryu.topology import event, switches
from ryu.topology.api import get_link, get_all_link
from ryu import utils
from ryu.lib import hub


# import sys
#
# sys.path.append('/home/fwy/Desktop/graph')
# import random_graph


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
        # self.net = random_graph.demo_graph()
        self.network = nx.Graph()
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(
        ofp_event.EventOFPErrorMsg,
        [HANDSHAKE_DISPATCHER, CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error_msg_handler(self, ev):
        msg = ev.msg
        self.logger.debug('OFPErrorMsg received: type=0x%02x code=0x%02x '
                          'message=%s', msg.type, msg.code,
                          utils.hex_array(msg.data))

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

    def _monitor(self):
        while True:
            hub.sleep(10)
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

    # @set_ev_cls(event.EventSwitchEnter)
    # def process_switch_enter(self, ev):
    #     dpid = ev.switch.dp.id
    #     link_list = get_all_link(self)
    #     print(f"all link of {dpid} >>> ")
    #     print(link_list)
    #     links = list()
    #     for link in link_list:
    #         links.append((link.src.dpid, link.dst.dpid,
    #                       {'port': link.src.port_no, link.src.dpid: link.src.port_no, link.dst.dpid: link.dst.port_no}))
    #         links.append((link.dst.dpid, link.src.dpid,
    #                       {'port': link.dst.port_no, link.src.dpid: link.src.port_no, link.dst.dpid: link.dst.port_no}))
    #         print("links %s %s: " % (link.src.dpid, link.dst.dpid), link.src.port_no)
    #
    #         self.network.add_node(link.src.dpid, connected=dict())
    #         self.network.add_node(link.dst.dpid, connected=dict())
    #         # print self.network.nodes
    #         self.network.nodes[link.src.dpid]['connected'][link.src.port_no] = link.dst.dpid
    #         self.network.nodes[link.dst.dpid]['connected'][link.dst.port_no] = link.src.dpid
    #
    #     print("links: ", links)
    #     self.network.add_edges_from(links)

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

    def send_group_mod(self, datapath, ):
        """Do load balance"""

        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        port_1 = 3
        actions_1 = [ofp_parser.OFPActionOutput(port_1)]

        port_2 = 2
        actions_2 = [ofp_parser.OFPActionOutput(port_2)]

        weight_1 = 50
        weight_2 = 50

        watch_port = ofproto_v1_3.OFPP_ANY
        watch_group = ofproto_v1_3.OFPQ_ALL

        buckets = [
            ofp_parser.OFPBucket(weight_1, watch_port, watch_group, actions_1),
            ofp_parser.OFPBucket(weight_2, watch_port, watch_group, actions_2)]

        group_id = 50
        req = ofp_parser.OFPGroupMod(
            datapath, ofp.OFPFC_ADD,
            ofp.OFPGT_SELECT, group_id, buckets)

        datapath.send_msg(req)

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

        if eth.ethertype == ether_types.ETH_TYPE_IPV6 or \
                eth.ethertype == ether_types.ETH_TYPE_LLDP:
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
                self.logger.info("Dpid is not in mac_to_port")
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
                path = nx.shortest_path(self.network, dpid, 7)
                if len(path) > 1:
                    next_node = path[1]
                    if self.network.has_edge(dpid, next_node):
                        self.logger.info("next to %s", next_node)
                        out_port = self.network[dpid][next_node]['dpid_to_port'][next_node]
                        self.logger.info("out port is %s", out_port)
                        actions = [parser.OFPActionOutput(out_port)]
                        self.send_packet_out(datapath, msg, actions)

