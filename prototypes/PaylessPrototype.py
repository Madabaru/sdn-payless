import os
import sys
from g3_payless.framework.MonitoringFramework import MonitoringFramework
from g3_payless.monitoring.algorithms import algorithm_by_name
from g3_payless.routing.DijkstraRouting import DijkstraRouting
# noinspection PyUnresolvedReferences
from ryu.controller.ofp_event import EventOFPSwitchFeatures
from ryu.ofproto.ofproto_v1_3_parser import OFPMatch, OFPActionOutput
from ryu.lib.packet import ether_types
from ryu.lib.packet.packet import Packet
from ryu.lib.packet.ipv4 import ipv4


class PaylessPrototype(MonitoringFramework):
    """
    Prototype SDN application using the g3_payless framework
    """

    def __init__(self, *args, **kwargs):
        """
        Reads environment variables and interprets them accordingly
        Environment variables can specify:
            * Which monitoring algorithm to use
            * Where to store statistics
            * The network topology file
        :param args: Positional Arguments
        :type args: list
        :param kwargs: Keyword Arguments
        :type kwargs: dict
        """
        self.algorithm_name = os.environ.get("ALGO", "payless")
        super(PaylessPrototype, self).__init__(*args, **kwargs)

        stats_file_path = os.environ.get("STATS_FILE")
        if stats_file_path is None:
            algo_name = self.algorithm.__class__.__name__
            stats_file_path = "artifacts/stats-{}.json".format(algo_name)
        self.STATS_FILE = stats_file_path

        topology_file = os.environ["TOPOLOGY_FILE"]
        self.routing_algo = DijkstraRouting(topology_file)

    def define_algorithm(self):
        """
        Specifies the monitoring algorithm to use
        :return: None
        :rtype: None
        """
        algo = None
        for algo_name, algo_cls in algorithm_by_name.items():
            if self.algorithm_name == algo_name:
                params = {"app": self}
                if "payless" in algo_name:
                    params.update({
                        "tau_min": int(os.environ["PAYLESS_TAU_MIN"]),
                        "tau_max": int(os.environ["PAYLESS_TAU_MAX"]),
                        "alpha": int(os.environ["PAYLESS_ALPHA"]),
                        "beta": int(os.environ["PAYLESS_BETA"]),
                        "delta_1": int(os.environ["PAYLESS_DELTA_1"]),
                        "delta_2": int(os.environ["PAYLESS_DELTA_2"])
                    })
                algo = algo_cls(**params)
                break
        if algo is None:
            self.logger.error("Invalid algorithm")
            sys.exit(1)
        return algo

    def handle_packet_in(self, event):
        """
        Installs flow rules for incoming packets using Dijkstra
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :return: Any generated flow IDs
        :rtype: list
        """
        message = event.msg
        datapath = message.datapath
        switch_id = datapath.id
        packet = Packet(message.data)
        ipv4_info = packet.get_protocol(ipv4)
        if ipv4_info is None:
            return []

        out_port, src_subnet, dst_subnet = \
            self.routing_algo.calculate_routing_decision(
                switch_id, ipv4_info.src, ipv4_info.dst
            )
        match = OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP,
            ipv4_src=src_subnet,
            ipv4_dst=dst_subnet
        )

        # If packets come in very quickly, the flow rule may not be installed
        # yet. To avoid creating new flows, we check if the flow rules were
        # already registered in active_flows.
        for existing_flow in self.active_flows.values():
            if existing_flow.is_ipv4_match_equal(switch_id, match):
                self.send_pkt(datapath, message.data, out_port)
                return []

        actions = [OFPActionOutput(out_port)]
        flow_id = self.program_flow(
            datapath=datapath,
            match=match,
            actions=actions,
            priority=10,
            hard_timeout=120,
            idle_timeout=5
        )
        self.send_pkt(datapath, message.data, out_port)
        return [flow_id]
