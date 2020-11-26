from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
import ryu.ofproto.ofproto_v1_3_parser as parser
import ryu.ofproto.ofproto_v1_3 as ofproto
from ryu.lib.packet import packet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ethernet, arp, ipv4, ipv6, tcp

from cockpit import CockpitApp
from netaddr import IPAddress, IPNetwork

# Hosts
H1 = ('11.0.0.0', '255.0.0.0')
H8 = ('88.0.0.0', '255.0.0.0')

H2 = ('22.0.0.0', '255.0.0.0')
H7 = ('77.0.0.0', '255.0.0.0')

H3 = ('33.0.0.0', '255.0.0.0')
H6 = ('66.0.0.0', '255.0.0.0')

# Note: dp.id is sw-ID + 1
ROUTING_TABLE = [
    # H1 -> H8
    (H1, H8, 4, 2, 1),
    (H1, H8, 2, 2, 1),
    (H1, H8, 1, 1, 2),
    (H1, H8, 3, 1, 3),
    (H1, H8, 7, 1, 3),
    # H2 -> H7
    (H2, H7, 4, 2, 1),
    (H2, H7, 2, 2, 1),
    (H2, H7, 1, 1, 2),
    (H2, H7, 3, 1, 3),
    (H2, H7, 7, 1, 2),
    # H3 -> H6
    (H3, H6, 5, 3, 1),
    (H3, H6, 2, 2, 1),
    (H3, H6, 1, 1, 2),
    (H3, H6, 3, 1, 2),
    (H3, H6, 6, 1, 3),
]

# ROUTING_TABLE = ROUTING_TABLE + [(dst, src, sid, out_port, in_port) for (src, dst, sid, in_port, out_port) in ROUTING_TABLE]

class PaylessApp(CockpitApp):
    def __init__(self, *args, **kwargs):
        super(PaylessApp, self).__init__(*args, **kwargs)
        self.info('Payless Ryu Controller')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        dp = ev.msg.datapath
        # r: src, dst, sid, in_port, out_port
        rules = [r for r in ROUTING_TABLE if r[2] == dp.id]
        for r in rules:
            match = parser.OFPMatch(
                eth_type = ether_types.ETH_TYPE_IP,
                ipv4_src = r[0],
                ipv4_dst = r[1]
            )
            actions = [parser.OFPActionOutput(r[4])]
            self.program_flow(dp, match, actions, priority=10, hard_timeout=0, idle_timeout=0)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        pass
