"""
@package simulator
simulator module
"""

#import time
import socket
import struct
import sys
from datetime import datetime

import logging as lg
lg.basicConfig(level=lg.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
lg.critical('Critical messages enabled.')
lg.error('Error messages enabled.')
lg.warning('Warning message enabled.')
lg.info('Informative message enabled.')
lg.debug('Low-level debug message enabled.')

class Simulator_stuff:

    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    FEEDBACK = {}

    RECV_LIST = None
    #LOCK = ""

class Simulator_socket:

    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, family=None, typ=None, sock=None):
        if sock is None:
            self.sock = socket.socket(family, typ)
            self.family = family
        else:
            self.sock = sock
            self.family = sock.family
        self.now = datetime.now() + "/"
    
    #def set_id(self, id):
    #    self.id = id

    #def set_max_packet_size(self, size):
    #    self.max_packet_size = size

    def send(self, msg):
        lg.debug("{} => {}".format(msg, self.sock))
        return self.sock.send(msg)

    def recv(self, msg_length):
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        lg.debug("{} <= {}".format(self.sock, msg))
        return msg

    def sendall(self, msg):
        lg.debug("{} => {}".format(msg, self.sock))
        return self.sock.sendall(msg)
        
    def sendto(self, msg, address):
        lg.debug("{} -> {} ({})".format(msg, address, self.sock))
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, now + address + "_udp")
        except ConnectionRefusedError:
            lg.error("simulator_stuff.sendto: the message {} has not been delivered because the destination {} left the team".format(msg, address))
        except KeyboardInterrupt:
            lg.warning("simulator_stuff.sendto: send_packet {} to {}".format(msg, address))
        except FileNotFoundError:
            lg.error("simulator_stuff.sendto: {}".format(now + address + "_udp"))
        except BlockingIOError:
            raise

    def recvfrom(self, max_mag_length):
        msg, sender = self.sock.recvfrom(max_msg_length)
        lg.debug("{} <- {} ({})".format(msg, sender, self.id))
        return (msg, sender)

    def connect(self, address):
        lg.debug("path {}".format(address))
        return self.sock.connect(now + address + "_tcp")

    def accept(self):
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer.replace(now, "").replace("_tcp", "").replace("udp", ""))

    def bind(self, address):
        if self.family == sock.SOCK_STREAM:
            return self.sock.bind(now + address + "_tcp")
        else:
            return self.sock.bind(now + address + "_udp")

    def listen(self, n):
        return self.sock.listen(n)

    def close(self):
        return self.sock.close() # Should delete files

    def settimeout(self, value):
        return self.sock.settimeout(value)
