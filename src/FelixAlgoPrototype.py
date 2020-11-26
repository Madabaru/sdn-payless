#tm task=timedmirror

# Import dependencies for Ryu
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
import ryu.ofproto.ofproto_v1_3_parser as parser
import ryu.ofproto.ofproto_v1_3 as ofproto
from ryu.lib.packet import packet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ethernet, arp, ipv4, ipv6
from ryu.lib import hub

# Import 3rd party dependencies
from operator import attrgetter
from netaddr import IPAddress, IPNetwork
import time
import random
import logging
import json

JSON_FILE = 'data.json'

class FelixAlgoPrototype(app_manager.RyuApp):
    
    def __init__(self, *args, **kwargs):
        super(FelixAlgoPrototype, self).__init__(*args, **kwargs)

        # Instantiate the Scheduling Algorithm
        self.monitoring_algorithm = MonitoringAlgorithm(FelixAlgoPrototype)


    # Install a flow on a switch
    def install_flow(self, dp, ip_dst, out_port, cookie, priority=0, hard_timeout=0, idle_timeout=0):

        match = parser.OFPMatch(
            eth_type = ether_types.ETH_TYPE_IP,
            ipv4_dst = (ip_dst, '255.0.0.0')
            )
        action = [parser.OFPActionOutput(out_port)]
        instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action)]
            
        flowmod = parser.OFPFlowMod(dp, 
            match=match,
            instructions=instruction,
            priority=priority,
            hard_timeout=hard_timeout,
            idle_timeout=idle_timeout,
            cookie=cookie, 
            flags=dp.ofproto.OFPFF_SEND_FLOW_REM)

        dp.send_msg(flowmod)


    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        msg = ev.msg
        dp = msg.datapath

        # Install default flow rule
        match = parser.OFPMatch()
        action = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action)]
            
        flowmod = parser.OFPFlowMod(dp, 
            match=match,
            instructions=instruction,
            priority=0,
            hard_timeout=0,
            idle_timeout=0,
            cookie=0)

        dp.send_msg(flowmod)

        # Install flow rule 1
        match = parser.OFPMatch(
            eth_type = ether_types.ETH_TYPE_IP,
            ipv4_dst = ('22.0.0.0', '255.0.0.0')
            )
        action = [parser.OFPActionOutput(2)]
        instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action)]
        
        flowmod = parser.OFPFlowMod(dp, 
            match=match,
            instructions=instruction,
            priority=3,
            hard_timeout=0,
            idle_timeout=0,
            cookie=1)

        dp.send_msg(flowmod)

        # Install flow rule 2
        match = parser.OFPMatch(
            eth_type = ether_types.ETH_TYPE_IP,
            ipv4_dst = ('33.0.0.0', '255.0.0.0')
            )
        action = [parser.OFPActionOutput(3)]
        instruction = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, action)]
        
        flowmod = parser.OFPFlowMod(dp, 
            match=match,
            instructions=instruction,
            priority=3,
            hard_timeout=0,
            idle_timeout=0,
            cookie=2)

        dp.send_msg(flowmod)


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg
        dp = msg.datapath
        data = ev.msg.data
        pkt = packet.Packet(data)
        ip = pkt.get_protocol(ipv4.ipv4) 

        net = IPNetwork(ip.dst + '/8')
        subnet = net.network

        self.install_flow(dp, subnet, 4, self.monitoring_algorithm.cookie, 2, hard_timeout=1)

        self.monitoring_algorithm.handle_packet_in(ev)


    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):

        self.monitoring_algorithm.handle_state_change(ev)


    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        
        self.monitoring_algorithm.handle_flow_statistics_reply(ev)


    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        
        self.monitoring_algorithm.handle_flow_removed(ev)


class MonitoringAlgorithm():

    def __init__(self, ryu_app):
        self.app = ryu_app
        self.datapaths = []
        self.schedule_table = {}
        self.T_min = 10   # 250
        self.T_max = 1000
        self.delta_1 = 100
        self.delta_2 = 100
        self.alpha = 2
        self.beta = 6
        self.cookie = 3
        self.threads = {}
        self.U = None
        print 'MonitoringAlgorithm'


    @property
    def cookie(self):
        return self.cookie


    def monitor(self, key):

        while True:

            flows = self.schedule_table[key]
            for flow in flows:
                self.request_stats(flow['dp'], cookie=flow['cookie'])

            # Issue statistical information every tau seconds
            hub.sleep(10)


    def request_stats(self, datapath, cookie):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath, cookie=cookie)
        datapath.send_msg(req)


    def handle_state_change(self, event):

        datapath = event.datapath
        connected, flows = self.check_connecton(datapath.id)

        if event.state == MAIN_DISPATCHER:
            if not connected:
                pass

        elif event.state == DEAD_DISPATCHER:
            if connected:
                print 'HandleStateChange:unregister_datapath' + str(datapath.id)
                for flow in flows:
                    if flow['tau'] in self.schedule_table[flow['tau']]:
                        self.schedule_table[flow['tau']].remove(flow)
                        if len(self.schedule_table[flow['tau']]) == 0:
                            del self.schedule_table[flow['tau']]


    def check_connecton(self, id):
        flows = []
        for key in self.schedule_table.keys():
            for flow in self.schedule_table[key]:
                if flow['switch'] == id:
                    flows.append(flow)
        
        if not flows:
            return False, None
        else:
            return True, flows


    def handle_packet_in(self, event):

        # print 'MonitoringAlgorithm:HandlePacketIn'

        msg = event.msg
        dp = msg.datapath

        # Create new flow 
        flow = {}
        flow['dp'] = dp
        flow['switch'] = dp.id
        flow['port'] = msg.match['in_port']
        flow['tau'] = self.T_min
        flow['byte_count'] = 0
        flow['duration'] = 0
        flow['cookie'] = self.cookie

        if self.T_min in self.schedule_table.keys():
            self.schedule_table[self.T_min].append(flow)
        else:
            
            self.schedule_table[self.T_min] = [flow]
            
            # Register new thread
            self.threads[self.T_min] = hub.spawn(lambda: self.monitor(self.T_min))
        
        # Update counter
        self.cookie += 1


    def handle_flow_removed(self, event):

        flow = self.get_flow(event.msg.cookie)

        if flow is not None:
        
            diff_byte_count = event.msg.byte_count - flow['byte_count']
            diff_duration = event.msg.duration_nsec - flow['duration']
            checkpoint = time.time()

            data = {}
            data['switch_id'] = flow['switch']
            data['cookie'] = flow['cookie']
            data['time'] = checkpoint
            data['duration'] = diff_duration
            data['byte_count'] = diff_byte_count

            # Write data to file
            with open(JSON_FILE, 'a') as f:
                    json.dump(data, f)
        
            self.schedule_table[flow['tau']].remove(flow)
            if len(self.schedule_table[flow['tau']]) == 0:
                del self.schedule_table[flow['tau']]
                hub.kill(self.threads[flow['tau']])
        
    
    def get_flow(self, cookie):

        for flows in self.schedule_table.values():
            for flow in flows:
                if flow['cookie'] == cookie:
                    return flow
        return None


    def handle_flow_statistics_reply(self, event):
        """ This methods takes care of flow statistics reply messages. """
        
        body = event.msg.body
        switch_id = event.msg.datapath.id

        for stat in body:

            flow = self.get_flow(stat.cookie)

            if flow is not None:

                diff_byte_count = stat.byte_count - flow['byte_count']
                diff_duration = stat.duration_nsec - flow['duration']
                checkpoint = time.time()

                data = {}
                data['switch_id'] = switch_id
                data['cookie'] = flow['cookie']
                data['time'] = checkpoint
                data['duration'] = diff_duration
                data['byte_count'] = diff_byte_count

                # Write data to file
                with open(JSON_FILE, 'a') as f:
                    json.dump(data, f)
            
                if diff_byte_count < self.delta_1:

                    new_tau = min(flow['tau'] * self.alpha, self.T_max)

                    # Move f to schedule_table[f.tau]
                    if flow in self.schedule_table[flow['tau']]:
                        self.schedule_table[flow['tau']].remove(flow)
                        if len(self.schedule_table[flow['tau']]) == 0:
                            del self.schedule_table[flow['tau']]
                            hub.kill(self.threads[flow['tau']])

                    flow['tau'] = new_tau

                    # print self.schedule_table

                    if flow['tau'] in self.schedule_table.keys():
                        self.schedule_table[flow['tau']].append(flow)
                    else:
                        self.schedule_table[flow['tau']] = [flow]
                        # Register new thread
                        self.threads[flow['tau']] = hub.spawn(lambda: self.monitor(flow['tau']))
                                    
                elif diff_byte_count > self.delta_2:

                    new_tau  = max(flow['tau'] / self.beta, self.T_min)

                    # Move f to schedule_table[f.tau]
                    if flow['tau'] in self.schedule_table[flow['tau']]:
                        self.schedule_table[flow['tau']].remove(flow)
                        if len(self.schedule_table[flow['tau']]) == 0:
                            del self.schedule_table[flow['tau']]
                            hub.kill(self.threads[flow['tau']])
                    
                    flow['tau'] = new_tau

                    if flow['tau'] in self.schedule_table.keys():
                        self.schedule_table[flow['tau']].append(flow)
                    else:
                        self.schedule_table[flow['tau']] = [flow]
                        # Register new thread
                        self.threads[flow['tau']] = hub.spawn(lambda: self.monitor(flow['tau']))




