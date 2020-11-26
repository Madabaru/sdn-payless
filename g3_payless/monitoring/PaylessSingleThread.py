# -*- coding: utf-8 -*-
import time
from g3_payless.monitoring.PaylessMultiThread import PaylessMultiThread


class PaylessSingleThread(PaylessMultiThread):
    """
    Implementation of the payless adaptive monitoring algorithm that uses
    a single background thread
    """

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        return "payless-single-thread"

    def background(self):
        """
        Periodically sends out FlowStatsRequests to the switches in accordance
        with the payless adaptive monitoring algorithm
        :return: None
        :rtype: None
        """
        next_deadlines = {}
        while True:

            self.add_missing_flows()

            now_ms = time.time() * 1000
            to_poll = []

            for tau in self.schedule_table.keys():
                if tau not in next_deadlines:
                    next_deadlines[tau] = now_ms + tau

            for tau, deadline in next_deadlines.items():
                if now_ms > deadline:
                    next_deadlines[tau] = now_ms + tau
                    for switch_id in self.schedule_table[tau].values():
                        to_poll.append(switch_id)

            self.logger.info("Sending stat requests to {}".format(to_poll))
            for switch in to_poll:
                self.app.send_flowstats_request(switch)

            if len(next_deadlines) > 0:
                next_deadline = min(next_deadlines.values())
            else:
                next_deadline = self.tau_min + now_ms

            diff_ms = abs(next_deadline - now_ms)
            diff_s = diff_ms / 1000
            time.sleep(diff_s)
