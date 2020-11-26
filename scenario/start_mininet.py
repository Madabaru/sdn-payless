from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.util import dumpNodeConnections

import sys
import time
import yaml
import os

# Note: reference to sync/remote/script_run_mininet.py

topology = None

if len(sys.argv) == 2:
    scenariofile = sys.argv[1]
    try:
        with open(scenariofile, "r") as file:
            parsed = yaml.safe_load(file.read())
            topology = parsed.get("root").get("topology")
    except Exception as e:
        print str(e)
        sys.exit(1)
else:
    print "usage: sudo python %s SCENARIOFILE" % sys.argv[0]
    sys.exit(1)

switches = topology.get("switches")
hosts = topology.get("hosts")
links = topology.get("links")

mn_dpids = 0
mn_switches = dict()
mn_hosts = dict()
mn_objects = dict()

net = Mininet(link=TCLink, waitConnected=True)
net.addController('c0', controller=RemoteController, ip='127.0.0.1',
    port=6633)

# create switches
for switch in switches:
    if not switch.get("enabled") == False:
        name = switch.get("name")
        s = net.addSwitch(name, dpid=str(switch.get("dpid", mn_dpids)))
        mn_switches[name] = s
        mn_objects[name] = s
        mn_dpids+=1

# create hosts
for host in hosts:
    name = host.get("name")
    mn_host = net.addHost(name, ip = host.get("ip"), defaultRoute = "dev {:s}-eth0".format(name))
    mn_hosts[name] = mn_host
    mn_objects[name] = mn_host

# create links
for link in links:
    if len(link) == 3:
        n1, n2, bandwitdh = link
        net.addLink(mn_objects[n1], mn_objects[n2], bw=bandwitdh)
    elif len(link) == 5:
        n1, p1, n2, p2, bandwitdh = link
        net.addLink(mn_objects[n1], mn_objects[n2], port1=p1, port2=p2,
            bw=bandwitdh)

net.start()
print "Dumping connections"
dumpNodeConnections(net.switches)
dumpNodeConnections(net.hosts)
CLI(net)
net.stop()
