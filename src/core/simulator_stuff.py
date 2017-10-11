"""
@package simulator
simulator module
"""

import time
import socket
import struct
import sys


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
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, msg, "S"))
        return self.sock.send(message)

    def sendall(self, fmt, msg):
        param = [msg.encode('utf-8') if type(msg) is str else msg][0]
        message = struct.pack(fmt, param)
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), "S", msg, self.id ))
        return self.sock.sendall(message)
        
    def sendto(self, fmt, msg, dst):
        params = [x.encode('utf-8') if type(x) is str else x for x in list(msg)]
        message = struct.pack(fmt, *params)
        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, msg, dst))
        try:
            sendto_value = self.sock.sendto(message, socket.MSG_DONTWAIT, "/tmp/"+dst+"_udp")
            print("SENDTO_VALUE", sendto_value)
            return sendto_value
        except ConnectionRefusedError:
            print("The message", msg, "has not been delivered because the destination", dst, "left the team")
        except KeyboardInterrupt:
            print("SENDTO_EXCEPT", fmt, msg, dst, message, params)
        except BlockingIOError:
            raise

    def recv(self, fmt):
        msg = self.sock.recv(struct.calcsize(fmt))
        try:
            msg_coded = struct.unpack(fmt, msg)[0]
        except struct.error:
            sys.stderr.write("ERROR: {} len {} expected {}".format(msg, len(msg), struct.calcsize(fmt)))

        message = [msg_coded.decode('utf-8').rstrip('\x00') if type(msg_coded) is bytes else msg_coded][0]
        if __debug__:
            print("{:.6f} {} <= [{}]".format(time.time(), self.id, message))
        return message

    def recvfrom(self, fmt):
        msg, sender = self.sock.recvfrom(struct.calcsize(fmt))
        try:
            msg_coded = struct.unpack(fmt, msg)
        except struct.error:
            sys.stderr.write("ERROR: {} len {} expected {}".format(msg, len(msg), struct.calcsize(fmt)))

        try:
            message = tuple([x.decode('utf-8').rstrip('\x00') if type(x) is bytes else x for x in msg_coded])
        except UnicodeDecodeError as e:
            sys.stderr.write("UNICODEERROR msg {} msg_coded{}\n".format(msg, msg_coded))
            sys.stderr.write("{}".format(e))
        sender = sender.replace("/tmp/", "").replace("_tcp", "").replace("_udp","")
        if __debug__:
            print("{:.6f} {} <- [{}] = {}".format(time.time(), self.id, message, sender))
        return (message, sender)

    def connect(self, path):
        print("path", path)
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
