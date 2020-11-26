"""Packet Length
mac dst  6B
mac src  6B
ip_proto 2B
ip_all  20B
udp_all  8B
payload 58B
-----------
total  100B
"""
# ip addr 4B
IP_H1 = "\x0B\x00\x00\x01" # 11.0.0.1
IP_H2 = "\x16\x00\x00\x01" # 22.0.0.1
IP_H3 = "\x21\x00\x00\x01" # 33.0.0.1
IP_H4 = "\x2c\x00\x00\x01" # 44.0.0.1
IP_H5 = "\x37\x00\x00\x01" # 55.0.0.1
IP_H6 = "\x42\x00\x00\x01" # 66.0.0.1
IP_H7 = "\x4d\x00\x00\x01" # 77.0.0.1
IP_H8 = "\x58\x00\x00\x01" # 88.0.0.1

# payload 58B
PAYLOAD = "\x00\x01"*29

MAC_H = (
    "\xcc\xcc\xcc\xcc\xcc\x01" # mac dst addr
    "\xcc\xcc\xcc\xcc\xcc\x02" # mac src addr
    "\x08\x00" # ip protocol
    )
IP_H = (
    "\x45\x00" # ip header
    "\x00\x56" # ip total length 20+8+8+50 = 86; hex(86)=0x56
    "\x00\x00" # ip ident
    "\x40\x00" # ip flag
    "\x40\x11" # ip ttl + ip udp
    "\xd7\x95" # ip checksum
    # "\x0B\x00\x00\x01" # ip src
    # "\x16\x00\x00\x01" # ip dst
    )
UDP_H = (
    "\x50\x00" # udp src port 20480
    "\x22\xB8" # udp dst port 8888
    "\x00\x16" # udp pkt length
    "\x00\x00" # udp checksum (can be zero)
    )

H1H8L800B = MAC_H + IP_H + IP_H1 + IP_H8 + UDP_H + PAYLOAD
H2H7L800B = MAC_H + IP_H + IP_H2 + IP_H7 + UDP_H + PAYLOAD
H3H6L800B = MAC_H + IP_H + IP_H3 + IP_H6 + UDP_H + PAYLOAD

packet_raw = {}
hosts = [IP_H1, IP_H2, IP_H3, IP_H4, IP_H5, IP_H6, IP_H7, IP_H8]
for src_host_id, src_host in enumerate(hosts):
    for dst_host_id, dst_host in enumerate(hosts):
        if src_host_id == dst_host_id:
            continue
        else:
            packet_name = \
                'h{}h{}l800b'.format(src_host_id + 1, dst_host_id + 1)
            packet_raw[packet_name] = \
                MAC_H + IP_H + src_host + dst_host + UDP_H + PAYLOAD

# packet_raw = {
#     'h1h8l800b': H1H8L800B,
#     'h2h7l800b': H2H7L800B,
#     'h3h6l800b': H3H6L800B,
# }
