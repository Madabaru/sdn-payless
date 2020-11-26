# -*- coding: utf-8 -*-
import time
import logging
# noinspection PyUnresolvedReferences
from ryu.controller.ofp_event import EventOFPFlowStatsReply, EventOFPPacketIn,\
    EventOFPFlowRemoved
from g3_payless.framework.RyuWrapper import RyuWrapper


class MonitoringAlgorithm(object):
    """
    General structure of a scheduling algorithm, meant to make scheduling
    algorithms easily exchangeable to ease comparing different scheduling
    algorithms
    """

    def __init__(self, app):
        """
        Initializes the Scheduling Algorithm
        :param app: The Ryu app that interfaces with the SDN controller
        :type app: RyuWrapper
        """
        self.app = app
        self.statistics = {}
        self.flow_states = {}
        self.logger = logging.getLogger(__name__)

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        raise NotImplementedError()

    def background(self):
        """
        Defines the scheduling algorithm's background behaviour
        :return: None
        :rtype: None
        """
        raise NotImplementedError()

    def handle_packet_in(self, event, flow_ids):
        """
        Defines how the scheduling algorithm handles PacketIn events
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :param flow_ids: IDs of flows that were installed in the process of
                         this PacketIn event
        :type flow_ids: list
        :return: None
        :rtype: None
        """
        raise NotImplementedError()

    def handle_flow_removed(self, event):
        """
        Defines how the scheduling algorithm handles FlowRemoved events
        :param event: The FlowRemoved event
        :type event: EventOFPFlowRemoved
        :return: None
        :rtype: None
        """
        raise NotImplementedError()

    def handle_flow_statistics_reply(self, event):
        """
        Defines how the scheduling algorithm handles FlowStatisticsReply events
        :param event: The FlowStatisticsReply event
        :type event: EventOFPFlowStatsReply
        :return: None
        :rtype: None
        """
        raise NotImplementedError()

    def insert_flow_stats(self, flow_id, total_bytes, duration_msec):
        """
        Stores collected flow statistics in self.statistics
        :param flow_id: The ID of the flow
        :type flow_id: int
        :param total_bytes: The total byte count of the flow
        :type total_bytes: int
        :param duration_msec: The total duration of the flow in milliseconds
        :type duration_msec: int
        :return: The byte count diff, the duration diff
        :rtype: tuple
        """

        if flow_id not in self.flow_states:
            self.flow_states[flow_id] = {
                "total_bytes": 0,
                "duration": 0
            }
        current = self.flow_states[flow_id]

        bytes_diff = total_bytes - current["total_bytes"]
        duration_diff = duration_msec - current["duration"]

        self.flow_states[flow_id] = {
            "total_bytes": total_bytes,
            "duration": duration_msec
        }

        if flow_id not in self.statistics:
            self.statistics[flow_id] = {}
        self.statistics[flow_id][time.time()] = {
            "bytes": bytes_diff,
            "duration": duration_diff,
            "total_bytes": current["total_bytes"],
            "total_duration": current["duration"]
        }

        self.logger.debug("[F{}] Stats: bytes={}, duration={}"
                          .format(flow_id, bytes_diff, duration_diff))

        return bytes_diff, duration_diff

    # noinspection PyMethodMayBeStatic
    def calculate_duration_msec(self, flowstats):
        """
        Calculates the duration of flow statistics in milliseconds, adding
        the nanoseconds part.
        :param flowstats: The flow statistics
        :type flowstats: OFPFlowStats
        :return: The duration in milliseconds
        :rtype: int
        """

        seconds = flowstats.duration_sec
        nanoseconds = flowstats.duration_nsec
        milliseconds = (seconds * 1000) + (nanoseconds / 1000000)
        return milliseconds

    def __str__(self):
        """
        :return: A string representation of the algorithm and its parameters
        """
        return self.name()
