import sys
import os
import time
import socket
import subprocess
import argparse

from packet_raw import packet_raw # packet definition

DEFAULT_DELAY = 3

def send_some_packets(interface, start, stop, step, number, packet, name=None, delay=None, reftime=None):
    """
    create socket and send udp packets according to the given parameters
    content of packet is defined in packet_raw.py
    """
    pid = os.getpid()
    if name == None:
        name = ''
    bytes_count = 0
    s = None
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    except socket.error, msg:
        print "[{}] {} Failed to create socket. {}".format(pid, name, msg)
        sys.exit(1)
    try:
        s.bind((interface, 0))
    except socket.error, msg:
        print "[{}] {} Bind failed. {}".format(pid, name, msg)
        sys.exit(1)
    print "[{}] {} socket ready".format(pid, name)

    # sleep to start point
    if reftime == None:
        reftime = time.time()
    if delay == None:
        delay = DEFAULT_DELAY
    time.sleep(max(0, reftime+start+delay-time.time()))

    # send packets and sleep to next time point
    t = time.time()
    print "[{}] {} start at {:.4f}".format(pid, name, t)
    rounds = int((stop-start)/step)
    for i in xrange(0, rounds):
        for j in xrange(0, number):
            bytes_count += s.send(packet_raw[packet])
        t2s = max((i+1)*step + t - time.time(), 0)
        time.sleep(t2s)
    print "[{}] {} {} bytes sent".format(pid, name, bytes_count)
    print "[{}] {} time spent: {:.4f}".format(pid, name, time.time()-t)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, required=False, help="name of the task")
    parser.add_argument('--interface', type=str, required=True, help="network interface to bind")
    parser.add_argument('--start', type=float, required=True, help="start time if task")
    parser.add_argument('--stop', type=float, required=True, help="end time of task")
    parser.add_argument('--step', type=float, required=True, help="send NUMBER of PACKET every STEP seconds")
    parser.add_argument('--number', type=int, required=True, help="packets to send every STEP")
    parser.add_argument('--packet', type=str, required=True, help="packet to send, hard-coded in packet_raw.py")
    parser.add_argument('--delay', type=float, required=False, help="sleep DELAY seconds before start, default to 3")
    parser.add_argument('--reftime', type=float, required=False, help="reference time as start point, default to NOW")
    args = parser.parse_args()
    send_some_packets(
            interface=args.interface,
            start=args.start, stop=args.stop, step=args.step,
            number=args.number, packet=args.packet,
            name=args.name, delay=args.delay, reftime=args.reftime
        )

