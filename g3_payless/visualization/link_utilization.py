# -*- coding: utf-8 -*-
import os
import json
# noinspection PyPackageRequirements
import matplotlib
from g3_payless.monitoring.PaylessMultiThread import PaylessMultiThread
from g3_payless.monitoring.PeriodicPollingPerFlow import PeriodicPollingPerFlow
from g3_payless.monitoring.FlowSense import FlowSense


def show_flow_stats(
        mode,
        flow_stats_files,
        only_ipv4_flows,
        smoothen_factor=1000,
        out_file=None,
        default_style=False
):
    """
    Visualizes link utilization using matplotlib
    :param mode: The mode for data visualization.
                 Currently supported are:
                    * per-flow
                    * per-ipv4
                    * total
    :type mode: str
    :param flow_stats_files: The files to visualize
    :type flow_stats_files: str
    :param only_ipv4_flows: Whether or not to only check ipv4-matched flows
    :type only_ipv4_flows: bool
    :param smoothen_factor: Averages (using the median value) the values in the
                            specified time interval in milliseconds
    :type smoothen_factor: int
    :param out_file: Optional file in which to store the generated graph
    :type out_file: str
    :return: None
    :rtype: None
    """
    colors = {
        PaylessMultiThread.name(): "blue",
        PeriodicPollingPerFlow.name(): "darkmagenta",
        FlowSense.name(): "black"
    }
    line_styles = {
        PaylessMultiThread.name(): "dashed",
        PeriodicPollingPerFlow.name(): "dotted",
        FlowSense.name(): "dashdot"
    }

    if out_file is not None:
        matplotlib.use("Agg")
    # noinspection PyPackageRequirements
    from matplotlib import pyplot
    figure = pyplot.figure(figsize=(7, 5))

    file_stats = {}
    algos = {}
    for _file in flow_stats_files:
        file_identifier = os.path.basename(_file).rsplit(".", 1)[0]
        stats, algo = load_stats(_file, only_ipv4_flows)
        stats = normalize_timestamps(stats)
        file_stats[file_identifier] = stats
        algos[file_identifier] = algo

    if mode == "per-flow":
        calculated_stats = calculate_per_flow_stats(file_stats)
        title = "Per-Flow Link Utilization"
    elif mode == "per-ipv4":
        calculated_stats = calculate_per_ipv4_match_stats(file_stats)
        title = "Per-IPv4-Match Link Utilization"
    elif mode == "total":
        calculated_stats = calculate_total_link_utilization(file_stats)
        title = "Total Link Utilization"
    else:
        print("Invalid Mode")
        return

    to_visualize = prepare_stats(calculated_stats, smoothen_factor)

    for identifier, datapoints in to_visualize.items():
        algo = algos[identifier]
        x_data = [point[0] for point in datapoints]
        y_data = [point[1] for point in datapoints]

        if algo in colors and algo in line_styles and not default_style:
            color = colors[algo]
            line_style = line_styles[algo]
            pyplot.step(
                x_data,
                y_data,
                label=identifier,
                linestyle=line_style,
                color=color
            )
        else:
            pyplot.step(x_data, y_data, label=identifier)

    pyplot.legend()
    pyplot.ylabel("Link Utilization (Bytes)")
    pyplot.xlabel("Time (s)")
    pyplot.title(title)

    if out_file is None:
        pyplot.show()
    else:
        figure.savefig(out_file, dpi=300)
    pyplot.close()


def load_stats(flow_stats_file, only_ipv4_flows):
    """
    Loads raw stats from a stats file
    :param flow_stats_file: The stats file to read
    :type flow_stats_file: str
    :param only_ipv4_flows: Whether or not to include only ipv4 flows or not
    :type only_ipv4_flows: bool
    :return: The prepared stats in the following format:
                {{flow_id: {info: {...}, data: {timestamp: bytes}}}
             as well as the name of the algorithm as second part of the tuple
    :rtype: tuplr
    """

    with open(flow_stats_file) as f:
        all_stats = json.load(f)

    flow_stats = all_stats["flow_stats"]
    flow_info = all_stats["flow_info"]
    stats = {}

    for flow_id, datapoints in flow_stats.items():
        flow = flow_info[flow_id]
        ipv4_src = flow["ipv4_src"]
        ipv4_dst = flow["ipv4_dst"]

        if only_ipv4_flows and ipv4_dst is None and ipv4_src is None:
            continue

        recorded = {}

        for timestamp, details in datapoints.items():
            flow_bytes = details["bytes"]
            flow_duration = details["duration"]
            end_millisecond = int(float(timestamp) * 1000)
            start_millisecond = end_millisecond - flow_duration
            milliseconds = list(range(start_millisecond, end_millisecond))

            if len(milliseconds) == 0:
                milliseconds = [end_millisecond]

            flow_bytes = int(flow_bytes / len(milliseconds))

            for millisecond in milliseconds:
                if millisecond not in recorded:
                    recorded[millisecond] = 0
                previous_max = recorded[millisecond]
                recorded[millisecond] = max(previous_max, flow_bytes)

        stats[flow_id] = {
            "info": flow,
            "data": recorded
        }

    return stats, all_stats.get("algorithm")


def calculate_per_flow_stats(file_stats):
    """
    Calculates statistics per flow
    :param file_stats: The previously prepared statistics
    :type file_stats: dict
    :return: The calculated statistics in the following format:
                 {flow_id: {timestamp_ms: bytes}}}
    :rtype: dict
    """

    per_flow_stats = {}

    for file_id, flow_stats in file_stats.items():
        for flow_id, flow in flow_stats.items():
            new_flow_id = file_id + "-" + flow_id
            per_flow_stats[new_flow_id] = flow["data"]

    return per_flow_stats


def calculate_per_ipv4_match_stats(file_stats):
    """
    Calculates statistics per flow, grouped by ipv4 match
    :param file_stats: The previously prepared statistics
    :type file_stats: dict
    :return: The calculated statistics in the following format:
                 {flow_id: {timestamp_ms: bytes}}}
    :rtype: dict
    """
    per_ipv4_stats = {}

    for file_id, flow_stats in file_stats.items():
        for flow_id, flow in flow_stats.items():
            ipv4_src = flow["info"]["ipv4_src"]
            ipv4_dst = flow["info"]["ipv4_dst"]
            new_flow_id = "{}-{}->{}".format(file_id, ipv4_src, ipv4_dst)

            if new_flow_id not in per_ipv4_stats:
                per_ipv4_stats[new_flow_id] = {}

            for timestamp, byte_count in flow["data"].items():
                if timestamp not in per_ipv4_stats[new_flow_id]:
                    per_ipv4_stats[new_flow_id][timestamp] = 0
                per_ipv4_stats[new_flow_id][timestamp] += byte_count

    return per_ipv4_stats


def calculate_total_link_utilization(file_stats):
    """
        Calculates total link utilization by file
        :param file_stats: The previously prepared statistics
        :type file_stats: dict
        :return: The calculated statistics in the following format:
                     {file_id: {timestamp_ms: bytes}}}
        :rtype: dict
        """

    total_stats = {}

    for file_id, flow_stats in file_stats.items():
        total_stats[file_id] = {}

        for _, flow in flow_stats.items():
            for timestamp, byte_count in flow["data"].items():
                if timestamp not in total_stats[file_id]:
                    total_stats[file_id][timestamp] = 0
                total_stats[file_id][timestamp] += byte_count

    return total_stats


def prepare_stats(calculated_stats, smoothen_factor):
    """
    Smooths out the calculated statistics and prepares them for
    visualization.
    :param calculated_stats: The previously calculated statistics
    :type calculated_stats: dict
    :param smoothen_factor: The length of the interval to which to smoothen
                            the data
    :type smoothen_factor: int
    :return: The prepared statistics in the following format:
                {label: [(timestamp, bytes)]}
    :rtype: dict
    """
    prepared = {}
    maximum_timestamp = 0

    for identifier, datapoints in calculated_stats.items():
        prepared[identifier] = []

        collected = {}

        for millisecond, byte_count in datapoints.items():
            new_timestamp = int(millisecond / smoothen_factor)

            if new_timestamp > maximum_timestamp:
                maximum_timestamp = new_timestamp

            if new_timestamp not in collected:
                collected[new_timestamp] = []
            collected[new_timestamp].append(byte_count)

        for new_timestamp, values in collected.items():
            value = sorted(values)[int(len(values) / 2)]  # median
            prepared[identifier].append((new_timestamp, value))

    for identifier in prepared:

        nonzero_timestamps = [x[0] for x in prepared[identifier]]
        for timestamp in range(0, maximum_timestamp):
            if timestamp not in nonzero_timestamps:
                prepared[identifier].append((timestamp, 0))

        prepared[identifier].sort(key=lambda x: x[0])

    return prepared


def normalize_timestamps(stats):
    """
    Normalizes the timestamps for statistics
    :param stats: The statistics
    :type stats: dict
    :return: The statistics with normalized timestamps
    :rtype: dict
    """

    normalized = {}

    start_time = 0
    for flow in stats.values():
        for timestamp in flow["data"].keys():
            if start_time == 0:
                start_time = timestamp
            else:
                start_time = min(start_time, timestamp)

    for flow_id, flow in stats.items():
        normalized[flow_id] = {
            "info": flow["info"],
            "data": {}
        }
        for timestamp, byte_count in flow["data"].items():
            normalized_timestamp = timestamp - start_time
            normalized[flow_id]["data"][normalized_timestamp] = byte_count

    return normalized
