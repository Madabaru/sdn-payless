import os
import json
# noinspection PyPackageRequirements
import matplotlib
from g3_payless.monitoring.PaylessMultiThread import PaylessMultiThread
from g3_payless.monitoring.PeriodicPollingPerFlow import PeriodicPollingPerFlow


def show_overhead_stats(mode, stats_files, out_file, default_style =False):
    """
    Visualizes overhead statistics using matplotlib
    :param mode: The mode in which to visualize the data
                 Currently available:
                    * cummulative
                    * relative
    :type mode: str
    :param stats_files: The statistics files to visualize
    :type stats_files: list
    :param out_file: Optional file in which to store the generated graph
    :type out_file: str
    :return: None
    """
    if out_file is not None:
        matplotlib.use("Agg")
    # noinspection PyPackageRequirements
    from matplotlib import pyplot
    figure = pyplot.figure(figsize=(10, 7))

    colors = {
        PaylessMultiThread.name(): "red",
        PeriodicPollingPerFlow.name(): "blue"
    }
    line_styles = {
        PaylessMultiThread.name(): "dashed",
        PeriodicPollingPerFlow.name(): "dotted"
    }

    stats = {}
    algos = {}
    for stats_file in stats_files:
        with open(stats_file) as f:
            file_stats = json.load(f)
        file_id = os.path.basename(stats_file).rsplit(".", 1)[0]
        stats[file_id] = normalize(file_stats["overhead"])
        algos[file_id] = file_stats["algorithm"]

    if mode == "cummulative":
        to_display = cummulative(stats)
    elif mode == "relative":
        to_display = relative(stats)
    else:
        print("Invalid mode")
        return

    for file_id, datapoints in to_display.items():
        algo = algos[file_id]
        x_data = [point[0] for point in datapoints]
        y_data = [point[1] for point in datapoints]

        if algo in colors and algo in line_styles and not default_style:
            color = colors[algo]
            line_style = line_styles[algo]
            pyplot.plot(
                x_data,
                y_data,
                ".-",
                label=file_id,
                linestyle=line_style,
                color=color
            )
        else:
            pyplot.plot(x_data, y_data, label=file_id)

    pyplot.legend()
    pyplot.ylabel("Overhead (Number of FlowStatRequests)")
    pyplot.xlabel("Time (s)")
    pyplot.title("Overhead ({})".format(mode.title()))
    if out_file is None:
        pyplot.show()
    else:
        figure.savefig(out_file, dpi=300)
    pyplot.close()


def normalize(stats):
    """
    Normalizes the timestamps in the statistics
    :param stats: The statistics
    :type stats: dict
    :return: The statistics with normalized timestamps
    :rtype: dict
    """
    first = int(float(min(stats.keys())))
    normalized = {
        int(float(timestamp)) - first: value
        for timestamp, value in stats.items()
    }
    return normalized


def cummulative(stats):
    """
    Calculates cummulative overhead stats
    :param stats: The statistics
    :type stats: dict
    :return: The cummulative statistics
    :rtype: dict
    """
    return {
        file_id: [(x, y) for x, y in datapoints.items()]
        for file_id, datapoints in stats.items()
    }


def relative(stats):
    """
    Calculates relative overhead stats
    :param stats: The statistics
    :type stats: dict
    :return: The relative statistics
    :rtype: dict
    """
    relative_stats = {}
    for file_id, datapoints in stats.items():
        relative_stats[file_id] = []
        previous = 0
        for timestamp, value in datapoints.items():
            delta = value - previous
            relative_stats[file_id].append((timestamp, delta))
            previous = value

    return relative_stats
