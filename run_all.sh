#!/bin/bash

TODAY=$(date --iso-8601)
DATA="$TODAY/data"
PNG="$TODAY/png"
PDF="$TODAY/pdf"
[ -d "$TODAY" ] && echo "Directory $TODAY exists." && exit 1
mkdir "$TODAY"
mkdir "$DATA"
mkdir "$PNG"
mkdir "$PDF"

# Experiments
# Base Scenario
sudo python run_experiment.py scenario/topo-payless.yaml scenario/scene-payless.yaml payless periodicpolling flowsense -o "$DATA/base.json" -v
# Slow Scenario
sudo python run_experiment.py scenario/topo-payless.yaml scenario/scene-slow.yaml payless periodicpolling flowsense -o "$DATA/slow.json" -v
# Pause Scenario
sudo python run_experiment.py scenario/topo-payless.yaml scenario/scene-pause.yaml payless periodicpolling flowsense -o "$DATA/pause.json" -v

# Visualization
# Base Scenario
g3-link-utilization total "$DATA/"*base.json -o "$PNG/base-link-utilization.png"
g3-link-utilization total "$DATA/"*base.json -o "$PDF/base-link-utilization.pdf"
g3-overhead relative "$DATA/"*base.json -o "$PNG/base-relative-overhead.png"
g3-overhead relative "$DATA/"*base.json -o "$PDF/base-relative-overhead.pdf"

# Slow Scenario
g3-link-utilization total "$DATA/"*slow.json -o "$PNG/slow-link-utilization.png"
g3-link-utilization total "$DATA/"*slow.json -o "$PDF/slow-link-utilization.pdf"
g3-overhead relative "$DATA/"*slow.json -o "$PNG/slow-relative-overhead.png"
g3-overhead relative "$DATA/"*slow.json -o "$PDF/slow-relative-overhead.pdf"
g3-overhead cummulative "$DATA/payless-base.json" "$DATA/payless-slow.json" -o "$PNG/base-slow-overhead-cummulative-compare.png" --default-style
g3-overhead cummulative "$DATA/payless-base.json" "$DATA/payless-slow.json" -o "$PDF/base-slow-overhead-cummulative-compare.pdf" --default-style

# Pause Scenario
g3-link-utilization total "$DATA/"*pause.json -o "$PNG/pause-link-utilization.png"
g3-link-utilization total "$DATA/"*pause.json -o "$PDF/pause-link-utilization.pdf"
g3-overhead cummulative "$DATA/"*pause.json -o "$PNG/pause-cummulative-overhead.png"
g3-overhead cummulative "$DATA/"*pause.json -o "$PDF/pause-cummulative-overhead.pdf"
