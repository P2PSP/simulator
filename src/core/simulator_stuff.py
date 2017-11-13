"""
@package simulator
simulator module
"""

#import time
import socket
import struct
import sys
from datetime import datetime
import os

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
            self.type = typ
        else:
            self.sock = sock
            self.type = typ
        #self.now = str(datetime.now()) + "/"
        #os.mkdir(self.now)
    
    #def set_id(self, id):
    #    self.id = id

    #def set_max_packet_size(self, size):
    #    self.max_packet_size = size

    def send(self, msg):
        lg.debug("simulator_stuff.send: {} - [{}] => {}".format(self.sock.getsockname(), \
                                                              msg, \
                                                              self.sock.getpeername()))
        return self.sock.send(msg)

    def recv(self, msg_length):
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        lg.debug("simulator_stuff.recv: {} <= [{}] - {}".format(self.sock.getsockname(), \
                                                              msg, \
                                                              self.sock.getpeername()))
        return msg

    def sendall(self, msg):
        lg.debug("simulator_stuff.sendall: {} - [{}] => {}".format(self.sock.getsockname(), \
                                                                 msg, \
                                                                 self.sock.getpeername()))
        return self.sock.sendall(msg)
        
    def sendto(self, msg, address):
        lg.debug("simulator_stuff.sendto: {} - [{}] -> {}".format(address, \
                                                                msg, \
                                                                self.sock.getpeername()))
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, address + "_udp")
        except ConnectionRefusedError:
            lg.error("simulator_stuff.sendto: the message {} has not been delivered because the destination {} left the team".format(msg, address))
            raise
        except KeyboardInterrupt:
            lg.warning("simulator_stuff.sendto: send_packet {} to {}".format(msg, address))
            raise
        except FileNotFoundError:
            lg.error("simulator_stuff.sendto: {}".format(address + "_udp"))
            raise
        except BlockingIOError:
            raise

    def recvfrom(self, max_msg_length):
        msg, sender = self.sock.recvfrom(max_msg_length)
        sender = sender.replace("_tcp", "").replace("_udp", "")
        lg.debug("simulator_stuff.recvfrom: {} <- [{}] - {}".format(self.sock.getsockname(), \
                                                                  msg, \
                                                                  sender))
        return (msg, sender)

    def connect(self, address):
        lg.debug("simulator_stuff.connect({}): {}".format(address, self.sock))
        return self.sock.connect(address + "_tcp")

    def accept(self):
        lg.debug("simulator_stuff.accept(): {}".format(self.sock))
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer.replace("_tcp", "").replace("udp", ""))

    def bind(self, address):
        lg.debug("simulator_stuff.bind({}): {}".format(address, self.sock))
        if self.type == self.SOCK_STREAM:
            try:
                return self.sock.bind(address + "_tcp")
            except:
                lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address + "_tcp"))
                raise
        else:
            try:
                return self.sock.bind(address + "_udp")
            except:
                lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address + "_udp"))
                raise
       
    def listen(self, n):
        lg.debug("simulator_stuff.listen({}): {}".format(n, self.sock))
        return self.sock.listen(n)

    def close(self):
        lg.debug("simulator_stuff.close(): {}".format(self.sock))
        return self.sock.close() # Should delete files

    def settimeout(self, value):
        lg.debug("simulator_stuff.settimeout({}): {}".format(value, self.sock))
        return self.sock.settimeout(value)
