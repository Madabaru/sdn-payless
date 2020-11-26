# -*- coding: utf-8 -*-
from g3_payless.monitoring.PaylessMultiThread import PaylessMultiThread


class FlowSense(PaylessMultiThread):
    """
    Implementation of FlowSense monitoring
    Flowsense is basically payless adaptive monitoring that doesn't
    send out FlowStatsRequests
    """

    @classmethod
    def name(cls):
        """
        :return: The name of the algorithm
        :rtype: str
        """
        return "flowsense"

    def background(self):
        """
        Don't send out any FlowStatsRequests
        :return: None
        :rtype: None
        """
        pass

    def __str__(self):
        """
        :return: A string representation of the algorithm and its parameters
        """
        return self.name()
