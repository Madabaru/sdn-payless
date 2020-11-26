#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import time
import signal
import argparse
from subprocess import Popen

try:
    # noinspection PyUnresolvedReferences
    from g3_payless.monitoring.algorithms import algorithm_by_name
    algo_choices = set(list(algorithm_by_name.keys()))
except ImportError:
    algo_choices = {
        "payless",
        "periodicpolling",
        "flowsense"
    }

# Check for root:
if os.geteuid() != 0:
    print("This script must run as root")
    sys.exit(1)


parser = argparse.ArgumentParser()
parser.add_argument("topology_file", help="Path to the topology file")
parser.add_argument("scenario_file", help="Path to the scenario file")
parser.add_argument("algorithms", choices=algo_choices,
                    help="The monitoring alogithm to use", nargs="+")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="Increases output verbosity")
parser.add_argument("-d", "--debug", action="store_true",
                    help="Greatly increases output verbosity")
parser.add_argument("-o", "--out", default="stats.json",
                    help="The file in which to write the monitored stats")
parser.add_argument("--payless-tau-min", type=int, default=500,
                    help="Minimum Value for tau in the payless algorithm "
                         "in milliseconds")
parser.add_argument("--payless-tau-max", type=int, default=5000,
                    help="Maximum Value for tau in the payless algorithm "
                         "in milliseconds")
parser.add_argument("--payless-alpha", type=int, default=2,
                    help="The alpha value for the payless algorithm")
parser.add_argument("--payless-beta", type=int, default=6,
                    help="The beta value for the payless algorithm")
parser.add_argument("--payless-delta-1", type=int, default=1000000,
                    help="The delta 1 value for the payless algorithm "
                         "in bytes")
parser.add_argument("--payless-delta-2", type=int, default=1000000,
                    help="The delta 2 value for the payless algorithm "
                         "in bytes")
parser.add_argument("--runs", type=int, default=1)
args = parser.parse_args()


DEVNULL = open(os.devnull, "w")
topology_file = os.path.abspath(args.topology_file)
scenario_file = os.path.abspath(args.scenario_file)
prototype_file = os.path.abspath("prototypes/PaylessPrototype.py")

if args.debug:
    verbosity = 10
elif args.verbose:
    verbosity = 20
else:
    verbosity = 30
verbosity = str(verbosity)

os.environ["PAYLESS_TAU_MIN"] = str(args.payless_tau_min)
os.environ["PAYLESS_TAU_MAX"] = str(args.payless_tau_max)
os.environ["PAYLESS_ALPHA"] = str(args.payless_alpha)
os.environ["PAYLESS_BETA"] = str(args.payless_beta)
os.environ["PAYLESS_DELTA_1"] = str(args.payless_delta_1)
os.environ["PAYLESS_DELTA_2"] = str(args.payless_delta_2)

for algorithm in args.algorithms:
    print("Performing experiment for algorithm {}".format(algorithm))

    for run in range(0, args.runs):

        outfile = os.path.abspath(args.out)
        filename = os.path.basename(outfile)
        out_dir = os.path.dirname(outfile)

        if args.runs != 1:
            filename = str(run) + "-" + filename
        if len(args.algorithms) > 1:
            filename = algorithm + "-" + filename

        outfile = os.path.join(out_dir, filename)

        print("Cleaning up mininet")
        Popen(["mn", "-c"], stderr=DEVNULL, stdout=DEVNULL).wait()

        os.chdir("scenario")
        print("Starting mininet")
        mininet = Popen(["python", "start_mininet.py", topology_file],
                        stderr=DEVNULL, stdout=DEVNULL)
        time.sleep(5)

        os.environ["TOPOLOGY_FILE"] = topology_file
        os.environ["ALGO"] = algorithm
        os.environ["STATS_FILE"] = outfile
        print("Starting ryu")
        ryu = Popen([
            "ryu-manager", prototype_file, "--default-log-level", verbosity
        ])
        time.sleep(5)

        print("Starting traffic generation")
        traffic_cmd = ["python", "eval_payless.py", scenario_file]
        if args.verbose:
            traffic = Popen(traffic_cmd)
        else:
            traffic = Popen(traffic_cmd, stdout=DEVNULL)
        traffic.wait()
        time.sleep(15)

        print("Stopping ryu")
        ryu.send_signal(signal.SIGTERM)
        print("Stopping mininet")
        mininet.send_signal(signal.SIGTERM)
        ryu.wait()
        mininet.wait()
        os.chdir("..")
        time.sleep(5)

DEVNULL.close()
print("Done")
