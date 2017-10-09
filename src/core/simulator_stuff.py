"""
@package simulator
simulator module
"""

import time
import socket


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

    def send(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, "S" ))
        return self.sock.send(message)

    def sendall(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), "S", message, self.id ))
        return self.sock.sendall(message)
        
    def sendto(self, message, dst):
        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, message, dst))
        try:
            return self.sock.sendto(message, "/tmp/"+dst+"_udp")
        except ConnectionRefusedError:
            print("The message", message, "has not been delivered because the destination", dst, "left the team")

    def recv(self, length):
        message = self.sock.recv(length)
        if __debug__:
            print("{:.6f} {} <= [{}]".format(time.time(), self.id, message))
        return message

    def recvfrom(self, length):
        message, sender = self.sock.recvfrom(length)
        sender = sender.replace("/tmp/", "").replace("_tcp", "").replace("_udp","")
        # print("RECV_FROM", message, sender)
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
