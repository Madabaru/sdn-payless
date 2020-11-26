# -*- coding: utf-8 -*-
import time
from g3_payless.monitoring.PeriodicPollingPerFlow import PeriodicPollingPerFlow


class PeriodicPollingPerSwitch(PeriodicPollingPerFlow):
    """
    Monitoring Algorithm that periodically sends out FlowStatsRequest
    messages to the connected switches to collect statistics
    This implementation sends out FlowStatsRequests for each connected switch
    in set intervals
    """

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        return "periodicpolling-switches"

    def background(self):
        """
        Periodically sends out FlowStatsRequests to all switches
        :return: None
        :rtype None
        """
        while True:
            time.sleep(self.polling_interval)
            to_poll = [x for x in self.app.switches.keys()]
            self.logger.info("Sending stat requests to {}".format(to_poll))
            for switch_id in to_poll:
                self.app.send_flowstats_request(switch_id)
