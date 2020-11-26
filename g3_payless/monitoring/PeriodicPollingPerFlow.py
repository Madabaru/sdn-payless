# -*- coding: utf-8 -*-
import time
from g3_payless.framework.RyuWrapper import RyuWrapper
from g3_payless.monitoring.MonitoringAlgorithm import MonitoringAlgorithm


class PeriodicPollingPerFlow(MonitoringAlgorithm):
    """
    Monitoring Algorithm that periodically sends out FlowStatsRequest
    messages to the connected switches to collect statistics
    This implementation sends out FlowStatsRequests based on active flows
    """

    def __init__(self, app, polling_interval=1):
        """
        Initializes the scheduler
        :param app: The ryu application
        :type app: RyuWrapper
        :param polling_interval: The polling interval, default is one second
        :type polling_interval: int
        """
        super(PeriodicPollingPerFlow, self).__init__(app)
        self.polling_interval = polling_interval

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        return "periodicpolling-flows"

    def background(self):
        """
        Periodically sends out FlowStatsRequests for all active flows
        :return: None
        :rtype None
        """
        while True:
            time.sleep(self.polling_interval)
            to_poll = [x.switch_id for x in self.app.active_flows.values()]
            self.logger.info("Sending stat requests to {}".format(to_poll))
            for switch_id in to_poll:
                self.app.send_flowstats_request(switch_id)

    def handle_packet_in(self, event, flow_ids):
        """
        Not handled by this algorithm
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :param flow_ids: IDs of flows that were installed in the process of
                         this PacketIn event
        :type flow_ids: list
        :return: None
        :rtype: None
        """
        pass

    def handle_flow_removed(self, event):
        """
        Not handled by this algorithm
        :param event: The FlowRemoved event
        :type event: EventOFPFlowRemoved
        :return: None
        :rtype: None
        """
        flow_id = event.msg.cookie
        event_byte_count = event.msg.byte_count
        event_duration = self.calculate_duration_msec(event.msg)
        self.insert_flow_stats(flow_id, event_byte_count, event_duration)
        self.app.remove_flow(flow_id)

    def handle_flow_statistics_reply(self, event):
        """
        Interprets the flow statistics replies
        :param event: The FlowStatisticsReply event
        :type event: EventOFPFlowStatsReply
        :return: None
        :rtype: None
        """
        for flow in event.msg.body:
            flow_id = flow.cookie
            event_byte_count = flow.byte_count
            event_duration = self.calculate_duration_msec(flow)
            self.insert_flow_stats(flow_id, event_byte_count, event_duration)
