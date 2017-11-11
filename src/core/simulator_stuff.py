"""
@package simulator
simulator module
"""

#import time
import socket
import struct
import sys

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

class Socket_print:

    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, family=None, typ=None, sock=None):
        if sock is None:
            self.sock = socket.socket(family, typ)
        else:
            self.sock = sock
    
    def set_id(self, id):
        self.id = id

    def set_max_packet_size(self, fmts):
        max = 0
        for fmt in fmts:
            if max < struct.calcsize(fmt):
                max = struct.calcsize(fmt)
        self.max_packet_size = max

    def send(self, msg, fmt):
        lg.debug("{} = [{}] => {}".format(self.id, msg, "S"))
        #params = [x.encode('utf-8') if type(x) is str else x for x in list(msg)]
        msg = struct.pack(fmt, msg)
        return self.sock.send(msg)

    def recv(self, fmt):
        msg_length = struct.calcsize(fmt)
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        try:
            decoded_msg = struct.unpack(fmt, msg)[0]
        except struct.error:
            lg.error("ERROR: {} len {} expected {}".format(msg, len(msg), msg_length))
        lg.debug("{} <= [{}]".format(self.id, decoded_msg))
        return decoded_msg

    def sendall(self, msg, fmt):
        lg.debug("{} = [{}] => {}".format('S', msg, self.id )) # 'S' ?
        message = struct.pack(fmt, msg)
        return self.sock.sendall(message)
        
    def sendto(self, msg, fmt, dst):
        lg.debug("{} - [{}] -> {}".format(self.id, msg, dst))
        #params = [x.encode('utf-8') if type(x) is str else x for x in list(msg)]
        message = struct.pack(fmt, msg)
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, "/tmp/" + dst + "_udp")
        except ConnectionRefusedError:
            lg.error("The message {} has not been delivered because the destination {} left the team".format(msg, dst))
        except KeyboardInterrupt:
            lg.warning("simulator_stuff:send_packet {}".format(msg, dst))
        except BlockingIOError:
            raise

    def recvfrom(self):
        msg, sender = self.sock.recvfrom(self.max_packet_size)
        lg.debug("{} <- [{}] = {}".format(self.id, msg, sender))
        return (msg, sender)

    def connect(self, path):
        lg.debug("path {}".format(path))
        return self.sock.connect("/tmp/" + path + "_tcp")

    def accept(self):
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer.replace("/tmp/", "").replace("_tcp", "").replace("udp", ""))

    def bind(self, path):
        return self.sock.bind("/tmp/" + path)

    def listen(self, n):
        return self.sock.listen(n)

    def close(self):
        return self.sock.close()

    def settimeout(self, value):
        return self.sock.settimeout(value)
