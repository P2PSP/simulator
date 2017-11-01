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

    def send(self, fmt, msg):
        params = [x.encode('utf-8') if type(x) is str else x for x in list(msg)]
        message = struct.pack(fmt, *params)
        lg.debug("{} = [{}] => {}".format(self.id, msg, "S"))
        return self.sock.send(message)

    def sendall(self, fmt, msg):
        param = [msg.encode('utf-8') if type(msg) is str else msg][0]
        message = struct.pack(fmt, param)
        lg.debug("{} = [{}] => {}".format("S", msg, self.id ))
        return self.sock.sendall(message)
        
    def sendto(self, fmt, msg, dst):
        params = [x.encode('utf-8') if type(x) is str else x for x in list(msg)]
        message = struct.pack(fmt, *params)
        lg.debug("{} - [{}] -> {}".format(self.id, msg, dst))
        try:
            sendto_value = self.sock.sendto(message, socket.MSG_DONTWAIT, "/tmp/"+dst+"_udp")
            #print("SENDTO_VALUE", sendto_value)
            return sendto_value
        except ConnectionRefusedError:
            lg.error("The message {} has not been delivered because the destination {} left the team".format(msg, dst))
        except KeyboardInterrupt:
            lg.warning("SENDTO_EXCEPT {}".format(fmt, msg, dst, message, params))
        except BlockingIOError:
            raise

    def recv(self, fmt):
        msg = self.sock.recv(struct.calcsize(fmt))
        try:
            msg_coded = struct.unpack(fmt, msg)[0]
        except struct.error:
            lg.error("ERROR: {} len {} expected {}".format(msg, len(msg), struct.calcsize(fmt)))

        message = [msg_coded.decode('utf-8').rstrip('\x00') if type(msg_coded) is bytes else msg_coded][0]
        lg.debug("{} <= [{}]".format(self.id, message))
        return message

    def recvfrom(self, fmt):
        msg, sender = self.sock.recvfrom(struct.calcsize(fmt))
        try:
            msg_coded = struct.unpack(fmt, msg)
        except struct.error:
            lg.error("ERROR: {} len {} expected {}".format(msg, len(msg), struct.calcsize(fmt)))

        try:
            message = tuple([x.decode('utf-8').rstrip('\x00') if type(x) is bytes else x for x in msg_coded])
        except UnicodeDecodeError as e:
            lg.error("UNICODEERROR msg {} msg_coded{}\n".format(msg, msg_coded))
            lg.error("{}".format(e))
        sender = sender.replace("/tmp/", "").replace("_tcp", "").replace("_udp","")
        lg.debug("{} <- [{}] = {}".format(self.id, message, sender))
        return (message, sender)

    def connect(self, path):
        lg.info("path {}".format(path))
        return self.sock.connect("/tmp/"+path+"_tcp")

    def accept(self):
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer.replace("/tmp/", "").replace("_tcp", "").replace("udp",""))

    def bind(self, path):
        return self.sock.bind("/tmp/"+path)

    def listen(self, n):
        return self.sock.listen(n)

    def close(self):
        return self.sock.close()

    def settimeout(self, value):
        return self.sock.settimeout(value)
