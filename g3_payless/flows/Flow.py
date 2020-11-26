# -*- coding: utf-8 -*-


class Flow(object):
    """
    Class that eases keeping track of flows
    """

    def __init__(self, flow_id, switch_id, match, actions, priority):
        """
        Initializes the flow object
        :param flow_id: The ID of the flow
        :type flow_id: int
        :param switch_id: The ID of the switch the flow rule was installed on
        :type switch_id: int
        :param match: The match of the flow
        :type match: OFPMatch
        :param actions: The flow's actions
        :type actions: list
        :param priority: The priority of this flow
        :type priority: int
        """
        self.flow_id = flow_id
        self.switch_id = switch_id
        self.match = match
        self.actions = actions
        self.priority = priority

    @property
    def oxm_fields(self):
        """
        :return: The OXM fields of the match
        :rtype: dict
        """
        oxm_fields = [
            x["OXMTlv"] for x in
            self.match.to_jsondict()["OFPMatch"]["oxm_fields"]
        ]
        oxm_data = {
            val["field"]: (val["value"], val["mask"]) for val in oxm_fields
        }
        return oxm_data

    @property
    def src_ipv4(self):
        """
        :return: The source IPv4 address, if applicable (else None)
        :rtype: tuple
        """
        return self.oxm_fields.get("ipv4_src")

    @property
    def dst_ipv4(self):
        """
        :return: The destination IPv4 address, if applicable (else None)
        :rtype: tuple
        """
        return self.oxm_fields.get("ipv4_dst")

    def is_ipv4_match_equal(self, switch_id, match):
        """
        Checks if a given match is the same match as this one in regards to
        IPv4 source and destination
        :param switch_id: The ID of the switch of the match to check
        :type switch_id: int
        :param match: The match to check
        :type match: OFPMatch
        :return: True if equal, False if not equal
        :rtype: bool
        """
        other_flow = Flow(0, switch_id, match, [], 0)
        return switch_id == self.switch_id and \
            self.src_ipv4 == other_flow.src_ipv4 and \
            self.dst_ipv4 == other_flow.dst_ipv4

    def __json__(self):
        """
        :return: A dictionary representation of the flow
        :rtype: dict
        """
        return {
            "flow_id": self.flow_id,
            "switch_id": self.switch_id,
            "ipv4_src": self.src_ipv4,
            "ipv4_dst": self.dst_ipv4
        }
