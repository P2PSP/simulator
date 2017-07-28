"""
@package simulator
simulator module
"""

import time
import socket
import pickle

class Simulator_stuff:

    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    FEEDBACK = {}

    RECV_LIST = None
    #LOCK = ""


class Socket_print(socket.socket):

    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, family=socket.AF_UNIX, typ=socket.SOCK_DGRAM, proto=0, fileno=None, sock=None):
        if sock is None:
            socket.socket.__init__(self, family, typ, proto, fileno)
        else:
            pass
    
    def set_id(self, id):
        self.id = id

    def send(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, "S" ))
        return socket.socket.send(self, pickle.dumps(message))

    def sendall(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, "Peer" ))
        return socket.socket.sendall(self, pickle.dumps(message))
        
    def sendto(self, message, dst):
        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, message, dst))
        print("DDD", dst)
        return socket.socket.sendto(self, pickle.dumps(message), "/tmp/"+dst+"_udp")

    def recv(self, length):
        message = pickle.loads(socket.socket.recv(self, length))
        if __debug__:
            print("{:.6f} {} <= [{}]".format(time.time(), self.id, message))
        return message

    def recvfrom(self, length):
        message, sender = socket.socket.recvfrom(self, length)
        sender = sender.replace("/tmp/", "").replace("_tcp", "").replace("_udp","")
        message = pickle.loads(message)
        if __debug__:
            print("{:.6f} {} <- [{}] = {}".format(time.time(), self.id, message, sender))
        return (message, sender)

    def connect(self, path):
        print("path", path)
        return socket.socket.connect(self, "/tmp/"+path+"_tcp")

    def accept(self):
        peer_serve_socket, peer = socket.socket.accept(self)
        return (peer_serve_socket, peer.replace("/tmp/", "").replace("_tcp", "").replace("udp",""))

    def bind(self, path):
        return socket.socket.bind(self, "/tmp/"+path)
