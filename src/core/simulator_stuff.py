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


class Socket_queue:

    # UDP sockets for transmitting chunks from the splitter to the
    # peers. We should have so many UDP_SOCKETS as number of peers.
    UDP_SOCKETS = {}

    # TCP sockets for serving incomming peers.
    TCP_SOCKETS = {}

    def send(self, message, receiver):
        message = (message, self.id)
        Socket_queue.TCP_SOCKETS[receiver].put(message)
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, receiver))

    def recv(self):
        (message, sender) = Socket_queue.TCP_SOCKETS[self.id].get()
        if __debug__:
            print("{:.6f} {} <= [{}] = {}".format(time.time(), self.id, message, sender))
        return (message, sender)

    def sendto(self, message, receiver):
        message = (message, self.id)

        # Blocking 
        Socket_queue.UDP_SOCKETS[receiver].put((message))


        # Non-blocking
        #try:
        #    Socket_queue.UDP_SOCKETS[receiver].put_nowait((message))
        #except:
        #    print("simulator_stuff: warning, possible channel congestion!!!")

        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, message, receiver))

    # Blocking recvfrom
    def recvfrom(self):
        message = Socket_queue.UDP_SOCKETS[self.id].get()
        if __debug__:
            print("{:.6f} {} <- [{}]".format(time.time(), self.id, message))
        return message


class Socket_print(socket.socket):

    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM

    def set_id(self, id):
        self.id = id

    def send(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, "S" ))
        return socket.socket.send(self, message)

    def sendall(self, message):
        if __debug__:
            print("{:.6f} {} = [{}] => {}".format(time.time(), self.id, message, "Peer" ))
        return socket.socket.sendall(self, message)
        
    def sendto(self, message, dst):
        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, pickle.loads(message), dst))
        print("DDD", dst)
        return socket.socket.sendto(self, message, "/tmp/"+dst+"_udp")

    def recv(self, length):
        message = socket.socket.recv(self, length)
        if __debug__:
            print("{:.6f} {} <= [{}]".format(time.time(), self.id, message))
        return message

    def recvfrom(self, length):
        message, sender = socket.socket.recvfrom(self, length)
        if __debug__:
            print("{:.6f} {} <- [{}] = {}".format(time.time(), self.id, message, sender))
        return (message, sender.replace("/tmp/", "").replace("_tcp", "").replace("udp",""))

    def connect(self, path):
        return socket.socket.connect(self, "/tmp/"+path+"_tcp")

    def accept(self):
        peer_serve_socket, peer = socket.socket.accept(self)
        return (peer_serve_socket, peer.replace("/tmp/", "").replace("_tcp", "").replace("udp",""))

    def bind(self, path):
        return socket.socket.bind(self, "/tmp/"+path)
