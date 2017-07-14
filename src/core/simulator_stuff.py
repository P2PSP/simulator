"""
@package simulator
simulator module
"""

import time

class Simulator_stuff:

    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    FEEDBACK = {}

    LOCK = ""

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

    # Non-blocking sendto
    def sendto(self, message, receiver):
        message = (message, self.id)
        try:
            Socket_queue.UDP_SOCKETS[receiver].put((message))
        except:
            print("simulator_stuff: warning, possible channel congestion!!!")
        if __debug__:
            print("{:.6f} {} - [{}] -> {}".format(time.time(), self.id, message, receiver))

    # Blocking recvfrom
    def recvfrom(self):
        message = Socket_queue.UDP_SOCKETS[self.id].get()
        if __debug__:
            print("{:.6f} {} <- [{}]".format(time.time(), self.id, message))
        return message
