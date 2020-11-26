import socket
import sys

ETH_P_ALL = 3 # ALL PACKETS
ETH_P_IP = 0x800 # IP PACKETS

net_interface = ''
if len(sys.argv) == 2:
    net_interface = sys.argv[1]
else:
    print "usage: sudo python %s INTERFACE" % sys.argv[0]
    exit(1)

try :
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_IP))
except socket.error, msg :
    print 'Failed to create socket. ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

# Bind socket to local host and port
try:
    s.bind((net_interface, 0))
except socket.error , msg:
    print 'Bind failed. ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket ready'

#now keep talking with the client
while 1:
    d = s.recv(1024)
    if d == 0:
        raise RuntimeError("socket connection broken")
    else:
        print len(d), "bytes received"

s.close()
