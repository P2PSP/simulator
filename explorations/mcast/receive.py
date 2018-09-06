from selectors import select
import socket
import struct

#MCAST_GRP = '224.0.0.1'
MCAST_PORT = 5007

#socks = 2*[None]

#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock0 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock0.bind(('127.0.0.1', 9999))

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock1.bind(('', MCAST_PORT))  # use MCAST_GRP instead of '' to listen only

while True:
  ready_socks,_,_ = select.select([sock0, sock1], [], [])
  for sock in ready_socks:
    data, addr = sock.recvfrom(1024)
    print(data, addr, sock)

# to MCAST_GRP, not all groups on MCAST_PORT
#mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

#while True:
#  print(sock.recv(10240))
