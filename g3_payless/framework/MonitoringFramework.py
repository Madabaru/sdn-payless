# -*- coding: utf-8 -*-
import os
import json
import time
from threading import Thread
from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
# noinspection PyUnresolvedReferences
from ryu.controller.ofp_event import EventOFPFlowStatsReply, EventOFPPacketIn,\
    EventOFPFlowRemoved, EventOFPSwitchFeatures
from g3_payless.framework.RyuWrapper import RyuWrapper
from g3_payless.monitoring.MonitoringAlgorithm import MonitoringAlgorithm


class MonitoringFramework(RyuWrapper):
    """
    Ryu Application framework that uses a SchedulingAlgorithm
    to collect statistics.
    """

    STATS_FILE = "stats.json"
    """
    Specifies where to store the statistics
    """

    def define_algorithm(self):
        """
        Specifies the MonitoringAlgorithm to use
        :return: The MonitoringAlgorithm to use
        :rtype: MonitoringAlgorithm
        """
        raise NotImplementedError()

    def __init__(self, *args, **kwargs):
        """
        Initializes the scheduler and starts the background thread
        :param args: Positional Arguments
        :type args: list
        :param kwargs: Keyword Arguments
        :type kwargs: dict
        """
        super(MonitoringFramework, self).__init__(*args, **kwargs)
        self.overhead_datapoints = {}
        self.algorithm = self.define_algorithm()
        print("Using algorithm: {}".format(self.algorithm))
        self.threads = []
        self.start_background_threads()

    def start_background_threads(self):
        """
        Starts all background threads
        :return: None
        """
        self.threads = [
            Thread(target=self.algorithm.background),
            Thread(target=self.write_statistics),
            Thread(target=self.track_overhead)
        ]
        for thread in self.threads:
            thread.start()

    def track_overhead(self):
        """
        Periodically checks the overhead value and keeps track of it over time
        :return: None
        :rtype: None
        """
        while True:
            timestamp = time.time()
            self.overhead_datapoints[timestamp] = self.overhead_counter
            time.sleep(1)

    @set_ev_cls(EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _handle_flow_stats_reply(self, event):
        """
        Forwards FlowStatsReply messages to the scheduler
        :param event: The FlowStatsReply event
        :type event: EventOFPFlowStatsReply
        :return: None
        :rtype: None
        """
        self.logger.debug("[S{}] Handling FlowStatsReply"
                          .format(event.msg.datapath.id))
        self.handle_flow_stats_reply(event)
        self.algorithm.handle_flow_statistics_reply(event)

    def handle_flow_stats_reply(self, event):
        """
        This method may be overridden by child classes to easily add additional
        behaviour to the handling of FlowStatsReply messages
        :param event: The FlowStatsReply event
        :type event: EventOFPFlowStatsReply
        :return: None
        :rtype: None
        """
        pass

    @set_ev_cls(EventOFPPacketIn, MAIN_DISPATCHER)
    def _handle_packet_in(self, event):
        """
        Forwards PacketIn messages to the scheduler
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :return: None
        :rtype: None
        """
        self.logger.debug("[S{}] Handling PacketIn"
                          .format(event.msg.datapath.id))
        flows = self.handle_packet_in(event)
        self.algorithm.handle_packet_in(event, flows)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def handle_packet_in(self, event):
        """
        This method may be overridden by child classes to easily add additional
        behaviour to the handling of PacketIn messages
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :return: Any generated flow IDs
        :rtype: list
        """
        return []

    @set_ev_cls(EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _handle_flow_removed(self, event):
        """
        Forwards FlowRemoved messages to the scheduler
        :param event: The FlowRemoved event
        :type event: EventOFPFlowRemoved
        :return: None
        :rtype: None
        """
        self.logger.debug("[S{}] Handling FlowRemoved"
                          .format(event.msg.datapath.id))
        self.handle_flow_removed(event)
        self.algorithm.handle_flow_removed(event)

    def handle_flow_removed(self, event):
        """
        This method may be overridden by child classes to easily add additional
        behaviour to the handling of FlowRemoved messages
        :param event: The FlowRemoved event
        :type event: EventOFPFlowRemoved
        :return: None
        :rtype: None
        """
        pass

    def write_statistics(self):
        """
        Periodically writes statistics to the statistics file
        :return: None
        """
        while True:
            time.sleep(10)
            stats = {
                "flow_stats": self.algorithm.statistics,
                "overhead": self.overhead_datapoints,
                "flow_info": {
                    x: y.__json__()
                    for x, y in self.all_flows.items()
                },
                "algorithm": self.algorithm.name()
            }
            directory = os.path.dirname(self.STATS_FILE)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            with open(self.STATS_FILE, "w") as f:
                json.dump(stats, f, indent=4, sort_keys=True)
                self.logger.info("Wrote Stats to file")
