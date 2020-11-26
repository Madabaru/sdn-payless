# -*- coding: utf-8 -*-
import logging
from ryu.base.app_manager import RyuApp
from ryu.controller.controller import Datapath
from ryu.controller.handler import set_ev_cls, CONFIG_DISPATCHER
# noinspection PyUnresolvedReferences
from ryu.controller.ofp_event import EventOFPSwitchFeatures
from ryu.ofproto.ofproto_v1_3_parser import OFPMatch, OFPFlowMod, \
    OFPInstructionActions, OFPFlowStatsRequest, OFPActionOutput, \
    OFPSetConfig, OFPPacketOut
from ryu.ofproto.ofproto_v1_3 import OFPIT_APPLY_ACTIONS, \
    OFPFF_SEND_FLOW_REM, OFPP_CONTROLLER, OFPC_FRAG_NORMAL, OFPP_FLOOD, \
    OFP_NO_BUFFER
from g3_payless.flows.Flow import Flow


class RyuWrapper(RyuApp):
    """
    Wrapper around the RyuApp class that implements various quality of
    life improvements
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the ryu App.
        :param args: Positional Arguments
        :type args: list
        :param kwargs: Keyword Arguments
        :type kwargs: dict
        """
        super(RyuWrapper, self).__init__(*args, **kwargs)
        self.active_flows = {}
        self.removed_flows = {}
        self.switches = {}
        self.overhead_counter = 0
        self.logger = logging.getLogger(__name__)

    @property
    def all_flows(self):
        """
        :return: All active and removed flows
        :rtype: dict
        """
        all_flows = {}
        all_flows.update(self.active_flows)
        all_flows.update(self.removed_flows)
        return all_flows

    @set_ev_cls(EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _handle_switch_features(self, event):
        """
        Installs the default flow rule for every switch that connects
        to the controller
        :param event: The SwitchFeatures event
        :type event: EventOFPSwitchFeatures
        :return: None
        :rtype: None
        """
        datapath = event.msg.datapath
        self.logger.debug("[S{}] SwitchFeatures Event".format(datapath.id))
        self.switches[datapath.id] = datapath

        self.program_flow(
            datapath,
            OFPMatch(),
            [OFPActionOutput(OFPP_CONTROLLER)],
            0,
            0,
            0
        )
        datapath.send_msg(OFPSetConfig(
            datapath,
            OFPC_FRAG_NORMAL,
            0xffff
        ))
        self.handle_switch_features(event)

    def handle_switch_features(self, event):
        """
        Can be used by child classes to install additional proactive flow
        rules
        :param event: The SwitchFeatures event
        :type event: EventOFPSwitchFeatures
        :return: None
        :rtype: None
        """
        pass

    def program_flow(
            self,
            datapath,
            match,
            actions,
            priority=0,
            hard_timeout=600,
            idle_timeout=60
    ):
        """
        Install a new flow rule, while automatically adding the
        OFPFF_SEND_FLOW_REM flag as well as assigning the flow an ID
        and adding it to the flow rule as a cookie
        :param datapath: The datapath to the switch
        :type datapath: Datapath
        :param match: The OFP Match for the flow rule
        :type match: OFPMatch
        :param actions: The actions for the flow rule
        :type actions: list
        :param priority: The priority of the flow rule
        :type priority: int
        :param hard_timeout: The hard timeout of the flow rule
        :type hard_timeout: int
        :param idle_timeout: The idle timeout of the flow rule
        :type idle_timeout: int
        :return: The flow ID of the installed flow rule
        :rtype: int
        """
        if len(self.active_flows) == 0:
            flow_id = 0
        else:
            flow_id = max(self.active_flows.keys()) + 1
        flow_obj = Flow(flow_id, datapath.id, match, actions, priority)
        self.active_flows[flow_id] = flow_obj

        flowmod = OFPFlowMod(
            datapath,
            match=match,
            instructions=[
                OFPInstructionActions(
                    OFPIT_APPLY_ACTIONS,
                    actions
                )
            ],
            priority=priority,
            hard_timeout=hard_timeout,
            idle_timeout=idle_timeout,
            cookie=flow_id,
            flags=OFPFF_SEND_FLOW_REM
        )
        datapath.send_msg(flowmod)
        self.logger.info("[S{}] Install Flow Rule {}: {}"
                         .format(datapath.id, flow_id, match))
        return flow_id

    def send_flowstats_request(self, switch_id):
        """
        Send a request for flow statistics to a switch
        :param switch_id: The ID of the switch
        :type switch_id: int
        :return: None
        :rtype: None
        """
        self.logger.debug("Requesting flowstats from {}".format(switch_id))
        switch = self.switches[switch_id]
        req = OFPFlowStatsRequest(switch)
        switch.send_msg(req)
        self.overhead_counter += 1

    # noinspection PyMethodMayBeStatic
    def send_pkt(self, datapath, data, port=OFPP_FLOOD):
        """
        Convenience method that instructs a switch to forward
        a packet from the controller.
        :param datapath: The datapath to the switch from which to send
        :type datapath: Datapath
        :param data: The data to forward
        :type data:
        :param port: The port on which to forward
        :type port: int
        """
        self.logger.debug("[S{}] Forwarding packet on port {}"
                          .format(datapath.id, port))
        out = OFPPacketOut(
            datapath=datapath,
            actions=[OFPActionOutput(port)],
            in_port=OFPP_CONTROLLER,
            data=data,
            buffer_id=OFP_NO_BUFFER
        )
        datapath.send_msg(out)

    def remove_flow(self, flow_id):
        """
        Removes a flow from active_flows and moves it into removed_flows
        :param flow_id: The ID of the flow to remove
        :type flow_id: int
        :return: None
        :rtype: None
        """
        if flow_id in self.active_flows:
            self.logger.info("Removing Flow {}".format(flow_id))
            flow = self.active_flows.pop(flow_id)
            self.removed_flows[flow_id] = flow
