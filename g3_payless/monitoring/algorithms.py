# -*- coding: utf-8 -*-
from g3_payless.monitoring.FlowSense import FlowSense
from g3_payless.monitoring.PaylessSingleThread import PaylessSingleThread
from g3_payless.monitoring.PaylessMultiThread import PaylessMultiThread
from g3_payless.monitoring.PeriodicPollingPerFlow import PeriodicPollingPerFlow
from g3_payless.monitoring.PeriodicPollingPerSwitch import \
    PeriodicPollingPerSwitch


all_monitoring_algorithms = [
    FlowSense,
    PaylessMultiThread,
    PaylessSingleThread,
    PeriodicPollingPerFlow,
    PeriodicPollingPerSwitch
]


# Aliases for payless and periodicpolling
algorithm_by_name = {
    "payless": PaylessMultiThread,
    "periodicpolling": PeriodicPollingPerFlow
}

for algo in all_monitoring_algorithms:
    algorithm_by_name[algo.name()] = algo
