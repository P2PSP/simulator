import sys
import socket

MCAST_GRP = sys.argv[1]
MCAST_PORT = int(sys.argv[2])

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
sock.sendto(b"robot", (MCAST_GRP, MCAST_PORT))
