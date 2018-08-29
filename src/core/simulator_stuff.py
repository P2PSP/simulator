"""
@package simulator
simulator module
"""

# import time
import socket
import struct
import sys
from datetime import datetime
import os

# import logging as lg
import logging

# import coloredlogs
# coloredlogs.install()

class Simulator_stuff:
    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    FEEDBACK = {}

    RECV_LIST = None
    # LOCK = ""

    loglevel = logging.ERROR
    
class Simulator_socket():
    AF_INET = socket.AF_INET
    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, family=None, typ=None, sock=None):

        # lg.basicConfig(level=lg.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.lg = logging.getLogger(__name__)
        # handler = logging.StreamHandler()
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        # formatter = logging.Formatter(fmt='simulator_stuff.py - %(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',datefmt='%H:%M:%S')
        # handler.setFormatter(formatter)
        # self.lg.addHandler(handler)
        #self.lg.setLevel(logging.ERROR)
        self.lg.setLevel(Simulator_stuff.loglevel)
        # self.lg.critical('Critical messages enabled.')
        # self.lg.error('Error messages enabled.')
        # self.lg.warning('Warning message enabled.')
        # self.lg.info('Informative message enabled.')
        # self.lg.debug('Low-level debug message enabled.')

        if sock is None:
            self.sock = socket.socket(family, typ)
            self.type = typ
        else:
            self.sock = sock
            self.type = typ
            # self.now = str(datetime.now()) + "/"
            # os.mkdir(self.now)

    # def set_id(self, id):
    #    self.id = id

    # def set_max_packet_size(self, size):
    #    self.max_packet_size = size

    def send(self, msg):
        self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), \
                                              msg, \
                                              self.sock.getpeername()))
        return self.sock.send(msg)

    def recv(self, msg_length):
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        self.lg.info("{} <= [{}] - {}".format(self.sock.getsockname(), \
                                              msg, \
                                              self.sock.getpeername()))
        return msg

    def sendall(self, msg):
        self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), \
                                              msg, \
                                              self.sock.getpeername()))
        return self.sock.sendall(msg)

    def sendto(self, msg, address):
        self.lg.info("{} - [{}] -> {}".format(self.sock.getsockname(), \
                                              msg, \
                                              address))
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, address)
        except ConnectionRefusedError:
            self.lg.warning(
                "simulator_stuff.sendto: the message {} has not been delivered because the destination {} left the team".format(
                    msg, address))
        except KeyboardInterrupt:
            self.lg.warning("simulator_stuff.sendto: send_packet {} to {}".format(msg, address))
            raise
        except FileNotFoundError:
            self.lg.error("simulator_stuff.sendto: {}".format(address))
            raise
        except BlockingIOError:
            raise

    def recvfrom(self, max_msg_length):
        msg, sender = self.sock.recvfrom(max_msg_length)
        self.lg.info("{} <- [{}] - {}".format(self.sock.getsockname(), \
                                              msg, \
                                              sender))
        return (msg, sender)

    def connect(self, address):
        self.lg.info("simulator_stuff.connect({}): {}".format(address, self.sock))
        return self.sock.connect(address)

    def accept(self):
        self.lg.info("simulator_stuff.accept(): {}".format(self.sock))
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer)

    def bind(self, address):
        self.lg.info("simulator_stuff.bind({}): {}".format(address, self.sock))
        if self.type == self.SOCK_STREAM:
            try:
                return self.sock.bind(address)
            except:
                self.lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address))
                raise
        else:
            try:
                return self.sock.bind(address)
            except:
                self.lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address))
                raise

    def listen(self, n):
        self.lg.info("simulator_stuff.listen({}): {}".format(n, self.sock))
        return self.sock.listen(n)

    def close(self):
        self.lg.info("simulator_stuff.close(): {}".format(self.sock))
        return self.sock.close()  # Should delete files

    def settimeout(self, value):
        self.lg.info("simulator_stuff.settimeout({}): {}".format(value, self.sock))
        return self.sock.settimeout(value)

    #def timeout(self):
    #    self.lg.info("simulator_stuff: timeout on".format(self.sock))
    #    return self.sock.timeout

    def gethostbyname(name):
        return socket.gethostbyname(name)

    def gethostname():
        return socket.gethostname()

    def getsockname(self):
        return self.sock.getsockname()

    def ip2int(addr):                                                               
        return struct.unpack("!I", socket.inet_aton(addr))[0]                       


    def int2ip(addr):                                                               
        return socket.inet_ntoa(struct.pack("!I", addr))

def f(x):
    return (x*x)

def g(x):
    return (x*x*x)

def hash(addr):
    return chr(0x30+addr)

#def hash(addr):
#    if addr is None or len(addr)<2:
#        return '[]'
#    blk = addr[0].split('.')
#    bk = [int(x) for x in blk]
#    sh = bk[0]^f(bk[1])
#    sh = sh^g(bk[2])
#    sh = (sh + f(bk[3]))
#    sh = (sh + g(addr[1]))
#    return chr(33+sh%94)

