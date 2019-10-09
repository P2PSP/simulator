"""
@package simulator
simulator module
"""

# Latency has been simulated by delaying the reception of packets with
# a time.sleep(). However, by default, latency is disabled. In order
# to simulate it, uncoment the lines L0, L1, L2 and L3.

# Latency HAS BEEN DISABLED

latency = 0.005  # Seconds (L0)
#latency = 0.020

import time  # (L1)
import socket
import logging
import sys
import core.stderr as stderr

class Socket_wrapper():
    AF_INET = socket.AF_INET
    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM
    SOL_SOCKET = socket.SOL_SOCKET
    SO_REUSEADDR = socket.SO_REUSEADDR
    TimeoutException = socket.timeout
    ErrorException = socket.error
    gaierror = socket.gaierror

    def __init__(self, family=None, type=None, sock=None):
    #def __init__(self, family=None, type=None, sock=None):
        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        if __debug__:
            self.lg.setLevel(logging.DEBUG)
        else:
            self.lg.setLevel(logging.ERROR)

        if sock is None:
            self.sock = socket.socket(family, type)
            self.type = type
        else:
            self.sock = sock
            self.type = type
        try:
            self.lg.debug(f"{self.sock.getsockname()}: latency={latency}\n")
        except:
            self.lg.debug(f"{self.sock.getsockname()}: latency disabled\n")

    def send(self, msg):
        self.lg.debug(f"{self.sock.getsockname()} - [{msg}] => {self.sock.getpeername()}")
        return self.sock.send(msg)

    def sendall(self, msg):
        self.lg.debug(f"{self.sock.getsockname()} - [{msg}] => {self.sock.getpeername()}")
        return self.sock.sendall(msg)

    def sendto(self, msg, address):

        self.lg.debug(f"{self.sock.getsockname()} - [{msg}] --> {address}")
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, address)
        except ConnectionRefusedError:
            self.lg.error("sendto: connection refused from {address}")
        except KeyboardInterrupt:
            self.lg.warning("sendto: keyboard interrupt")
            raise
        except FileNotFoundError:
            self.lg.error("sendto: file not found")
            raise
        except BlockingIOError:
            raise

    def recv(self, msg_length):
        #time.sleep(latency)  # L2
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        self.lg.debug(f"{self.sock.getsockname()} <= [{msg}] - {self.sock.getpeername()}")
        return msg

    def recvfrom(self, max_msg_length):
        #time.sleep(latency)  # L3
        try:
            msg, sender = self.sock.recvfrom(max_msg_length)
            self.lg.debug(f"{self.sock.getsockname()} <-- [{msg}] - {sender}")
            return (msg, sender)
        except socket.timeout:
            raise

    def connect(self, endpoint):
        self.lg.debug(f"connected to {endpoint} ({self.sock})")
        return self.sock.connect(endpoint)

    def accept(self):
        self.lg.debug(f"accepted connection ({self.sock})")
        peer_serve_socket, peer = self.sock.accept()
        return (peer_serve_socket, peer)

    def bind(self, address):
        self.lg.debug(f"binding {address} ({self.sock})")
        try:
            return self.sock.bind(address)
        except:
            self.lg.error(f"bind: {sys.exc_info()[0]} when binding address \"{address}\"")
            raise

    def listen(self, n):
        self.lg.debug(f"listen({n}): {self.sock}")
        return self.sock.listen(n)

    def close(self):
        self.lg.debug(f"closing connection ({self.sock})")
        return self.sock.close()  # Should delete files

    def settimeout(self, value=1.0): # In seconds
        self.lg.debug(f"settimeout({value}): {self.sock}")
        return self.sock.settimeout(value)

    def gettimeout(self):
        timeout = self.sock.gettimeout()
        self.lg.debug(f"gettimeout({self.sock}): {timeout}")
        return timeout

    #def timeout(self):
    #    self.lg.debug("simulator_stuff: timeout on".format(self.sock))
    #    return self.sock.timeout

    def gethostbyname(name):
        return socket.gethostbyname(name)

    def gethostname():
        return socket.gethostname()

    def getsockname(self):
        return self.sock.getsockname()

    def getpeername(self):
        return self.sock.getpeername()

    def fileno(self):
        return self.sock.fileno()

    def setsockopt(self, level, optname, value):
        return self.sock.setsockopt(level, optname, value)

    def setblocking(self, value):
        return self.sock.setblocking(value)
