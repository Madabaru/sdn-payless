# -*- coding: utf-8 -*-
import time
from threading import Thread, Lock
from g3_payless.framework.RyuWrapper import RyuWrapper
from g3_payless.monitoring.MonitoringAlgorithm import MonitoringAlgorithm


class PaylessMultiThread(MonitoringAlgorithm):
    """
    Implementation of the monitoring algorithm presented by payless
    THis implementation uses one thread per bucket
    """

    def __init__(
            self,
            app,
            tau_min=500,
            tau_max=5000,
            alpha=2,
            beta=6,
            delta_1=1000000,
            delta_2=1000000
    ):
        """
        Initializes the algorithm
        Stores the parameters used to tweak the payless algorithm
        Initializes the schedule table

        :param app: The ryu application
        :type app: RyuWrapper
        :param tau_min: The minimum value for tau (polling interval)
        :type tau_min: int
        :param tau_max: The maximum value for tau (polling interval)
        :type tau_max: int
        :param alpha: The factor with which to multiply
        :type alpha: int
        :param beta: The factor with which to divide by
        :type beta: int
        :param delta_1: lower threshold
        :type delta_1: int
        :param delta_2: upper threshold
        :type delta_2: int
        """
        super(PaylessMultiThread, self).__init__(app)
        self.tau_min = tau_min
        self.tau_max = tau_max
        self.tau_start = int((tau_min + tau_max) / 2)
        self.alpha = alpha
        self.beta = beta
        self.delta_1 = delta_1
        self.delta_2 = delta_2

        self.schedule_table = {}
        self.scheduling_threads = {}
        self.schedule_lock = Lock()

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        return "payless-multi-thread"

    def monitor(self, tau):
        """
        Periodically requests flow statistics from the switches in accordance
        to a tau value as detailed in the payless adaptive monitoring
        algorithm
        :param tau: The tau value
        :type tau: int
        :return: None
        :rtype: None
        """
        self.logger.info("Starting monitoring thread for tau={}".format(tau))
        while True:
            tau_seconds = float(tau) / 1000.0
            time.sleep(tau_seconds)
            flows = self.schedule_table[tau]
            receiver_ids = [switch_id for switch_id in flows.values()]

            if len(receiver_ids) > 0:
                self.logger.info("Sending stat requests to {} for tau={}"
                                 .format(receiver_ids, tau))

            for switch_id in receiver_ids:
                self.app.send_flowstats_request(switch_id)

    def background(self):
        """
        Periodically checks if each tau entry in the scheduling table has
        its own monitoring thread and if not, starts it.
        :return: None
        :rtype: None
        """
        while True:
            time.sleep(1)
            self.add_missing_flows()
            for tau in self.schedule_table.keys():
                if tau not in self.scheduling_threads:
                    thread = Thread(target=lambda: self.monitor(tau))
                    thread.start()
                    self.scheduling_threads[tau] = thread

    def handle_packet_in(self, event, flow_ids):
        """
        Registers packets that were installed in the PacketIn event in the
        scheduling table.
        :param event: The PacketIn event
        :type event: EventOFPPacketIn
        :param flow_ids: The IDs of the installed flow rules
        :type flow_ids: list
        :return: None
        :rtype: None
        """
        message = event.msg
        datapath = message.datapath
        switch_id = datapath.id

        tau = self.tau_start

        self.schedule_lock.acquire()
        if tau not in self.schedule_table:
            self.schedule_table[tau] = {}
        for flow_id in flow_ids:
            self.schedule_table[tau][flow_id] = switch_id
        self.schedule_lock.release()

    def handle_flow_removed(self, event):
        """
        Handles removed flows. Removed flows are removed from the schedule
        table and statistics for the removed flow are recorded
        :param event: The FlowRemoved event
        :return: None
        """
        flow_id = event.msg.cookie
        event_byte_count = event.msg.byte_count
        event_duration = self.calculate_duration_msec(event.msg)
        self.insert_flow_stats(flow_id, event_byte_count, event_duration)
        self.app.remove_flow(flow_id)

        flow_info = self.get_flow_info(flow_id)
        if flow_info is not None:
            self.schedule_lock.acquire()
            self.schedule_table[flow_info["tau"]].pop(flow_id)
            self.schedule_lock.release()

    def handle_flow_statistics_reply(self, event):
        """
        Handles flow statistics replies.
        Statistics of the flows are recorded and the tau values
        are adjusted appropriately
        :param event: The FlowStatsReply event
        :return: None
        """
        for flow in event.msg.body:
            flow_id = flow.cookie
            event_byte_count = flow.byte_count
            event_duration = self.calculate_duration_msec(flow)

            diff_byte_count, diff_duration = self.insert_flow_stats(
                flow_id, event_byte_count, event_duration
            )

            flow_info = self.get_flow_info(flow_id)
            if flow_info is None:
                return
            tau = flow_info["tau"]

            if diff_byte_count < self.delta_1:
                new_tau = min(tau * self.alpha, self.tau_max)
            elif diff_byte_count > self.delta_2:
                new_tau = max(tau / self.beta, self.tau_min)
            else:
                new_tau = tau

            self.schedule_lock.acquire()

            if new_tau not in self.schedule_table:
                self.schedule_table[new_tau] = {}
            flow_info["tau"] = new_tau
            self.schedule_table[tau].pop(flow_id)
            self.schedule_table[new_tau][flow_id] = flow_info["switch_id"]

            self.schedule_lock.release()

    def get_flow_info(self, flow_id):
        """
        Retrieves information on a flow from the scheduling table.
        :param flow_id: The ID of the flow
        :type flow_id: int
        :return: The flow info, or None if it's not in the scheduling table
        :rtype: dict
        """
        for tau, flows in self.schedule_table.items():
            for _flow_id, switch_id in flows.items():
                if flow_id == _flow_id:
                    return {"switch_id": switch_id, "tau": tau}
        return None

    def add_missing_flows(self):
        """
        Makes sure that missing flows (i.e., proactive flows) are also
        tracked by payless.
        This is necessary to keep it fair towards the periodic polling
        approach.
        :return: None
        """
        # Make sure that proactive flows are also polled
        for id_to_check, active_flow in self.app.active_flows.items():
            included = False
            for flow_ids in self.schedule_table.values():
                for flow_id in flow_ids.keys():
                    if flow_id == id_to_check:
                        included = True
            if not included:
                self.logger.info("Adding missing flow rule {} to "
                                 "scheduling table".format(id_to_check))
                self.schedule_lock.acquire()
                if self.tau_start not in self.schedule_table:
                    self.schedule_table[self.tau_start] = {}
                self.schedule_table[self.tau_start][id_to_check] = \
                    active_flow.switch_id
                self.schedule_lock.release()

    def __str__(self):
        """
        :return: A string representation of the algorithm and its parameters
        """
        string = super(PaylessMultiThread, self).__str__() + "\n"
        for param, value in [
            ("tau_min", self.tau_min),
            ("tau_max", self.tau_max),
            ("alpha", self.alpha),
            ("beta", self.beta),
            ("delta_1", self.delta_1),
            ("delta_2", self.delta_2)
        ]:
            string += "{}: {}\n".format(param, value)
        return string
