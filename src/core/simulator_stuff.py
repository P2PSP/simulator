"""
@package simulator
simulator module
"""

# import time
import socket
import struct
import sys
from datetime import datetime
import os

# import logging as lg
import logging

from . import reed_solomon_codec


# import coloredlogs
# coloredlogs.install()

class Simulator_stuff:
    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    FEEDBACK = {}

    RECV_LIST = None
    # LOCK = ""


class Simulator_socket:
    AF_UNIX = socket.AF_UNIX
    SOCK_DGRAM = socket.SOCK_DGRAM
    SOCK_STREAM = socket.SOCK_STREAM
    MAX_MSG_MENGTH = 256
    ENCODE = False      # Bool. Signifies whether to use reed-solomon encoding or not

    def __init__(self, family=None, typ=None, sock=None):

        # lg.basicConfig(level=lg.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.lg = logging.getLogger(__name__)
        # handler = logging.StreamHandler()
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        # formatter = logging.Formatter(fmt='simulator_stuff.py - %(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',datefmt='%H:%M:%S')
        # handler.setFormatter(formatter)
        # self.lg.addHandler(handler)
        self.lg.setLevel(logging.ERROR)
        self.lg.critical('Critical messages enabled.')
        self.lg.error('Error messages enabled.')
        self.lg.warning('Warning message enabled.')
        self.lg.info('Informative message enabled.')
        self.lg.debug('Low-level debug message enabled.')

        if sock is None:
            self.sock = socket.socket(family, typ)
            self.type = typ
        else:
            self.sock = sock
            self.type = typ
            # self.now = str(datetime.now()) + "/"
            # os.mkdir(self.now)

    # def set_id(self, id):
    #    self.id = id

    # def set_max_packet_size(self, size):
    #    self.max_packet_size = size

    def send(self, msg):
        self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), msg, self.sock.getpeername()))
        if self.ENCODE:
            msg = reed_solomon_codec.encode(msg)
        return self.sock.send(msg)

    def recv(self, msg_length):
        msg = self.sock.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.sock.recv(msg_length - len(msg))
        if self.ENCODE:
            msg = reed_solomon_codec.decode(msg)
        self.lg.info("{} <= [{}] - {}".format(self.sock.getsockname(), msg, self.sock.getpeername()))
        return msg

    def sendall(self, msg):
        self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), msg, self.sock.getpeername()))
        if self.ENCODE:
            msg = reed_solomon_codec.encode(msg)
        return self.sock.sendall(msg)

    def sendto(self, msg, address):
        self.lg.info("{} - [{}] -> {}".format(self.sock.getsockname(), msg, address))
        if self.ENCODE:
            msg = reed_solomon_codec.encode(msg)
        try:
            return self.sock.sendto(msg, socket.MSG_DONTWAIT, address + "_udp")
        except ConnectionRefusedError:
            self.lg.error(
                "simulator_stuff.sendto: the message {} has not been delivered because the destination {} left the team".format(
                    msg, address))
            raise
        except KeyboardInterrupt:
            self.lg.warning("simulator_stuff.sendto: send_packet {} to {}".format(msg, address))
            raise
        except FileNotFoundError:
            self.lg.error("simulator_stuff.sendto: {}".format(address + "_udp"))
            raise
        except BlockingIOError:
            raise

    def recvfrom(self, max_msg_length):
        msg, sender = self.sock.recvfrom(max_msg_length)
        sender = sender.replace("_tcp", "").replace("_udp", "")
        if self.ENCODE:
            msg = reed_solomon_codec.decode(msg)
        self.lg.info("{} <- [{}] - {}".format(self.sock.getsockname(), msg, sender))
        return msg, sender

    def connect(self, address):
        self.lg.info("simulator_stuff.connect({}): {}".format(address, self.sock))
        return self.sock.connect(address + "_tcp")

    def accept(self):
        self.lg.info("simulator_stuff.accept(): {}".format(self.sock))
        peer_serve_socket, peer = self.sock.accept()
        return peer_serve_socket, peer.replace("_tcp", "").replace("udp", "")

    def bind(self, address):
        self.lg.info("simulator_stuff.bind({}): {}".format(address, self.sock))
        if self.type == self.SOCK_STREAM:
            try:
                return self.sock.bind(address + "_tcp")
            except:
                self.lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address + "_tcp"))
                raise
        else:
            try:
                return self.sock.bind(address + "_udp")
            except:
                self.lg.error("{}: when binding address \"{}\"".format(sys.exc_info()[0], address + "_udp"))
                raise

    def listen(self, n):
        self.lg.info("simulator_stuff.listen({}): {}".format(n, self.sock))
        return self.sock.listen(n)

    def close(self):
        self.lg.info("simulator_stuff.close(): {}".format(self.sock))
        return self.sock.close()  # Should delete files

    def settimeout(self, value):
        self.lg.info("simulator_stuff.settimeout({}): {}".format(value, self.sock))
        return self.sock.settimeout(value)

    # ------- Encoded message exchangers -------

    # def send_encoded(self, msg):
    #     self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), msg, self.sock.getpeername()))
    #     transmittable_message = reed_solomon_codec.encode(msg)
    #     # data_length = 0
    #     # start_message = "message_start_chunk_length %d" % len(transmittable_message)
    #     # self.sock.send(reed_solomon_codec.encode(start_message)[0])     # initial message specifying no of chunks
    #     # for message in transmittable_message:
    #     #     data_length += self.sock.send(message)
    #     # return data_length
    #     return self.sock.send(transmittable_message)
    #
    # def sendall_encoded(self, msg):
    #     self.lg.info("{} - [{}] => {}".format(self.sock.getsockname(), msg, self.sock.getpeername()))
    #     transmittable_message = reed_solomon_codec.encode(msg)
    #     self.sock.sendall(transmittable_message)
    #     # data_length = 0
    #     # start_message = "message_start_chunk_length %d" % len(transmittable_message)
    #     # self.sock.sendall(reed_solomon_codec.encode(start_message)[0])  # initial message specifying message length
    #     # for message in transmittable_message:
    #     #     data_length += self.sock.sendall(message)
    #     # return data_length
    #
    # def sendto_encoded(self, msg, address):
    #     self.lg.info("{} - [{}] -> {}".format(self.sock.getsockname(), msg, address))
    #     try:
    #         transmittable_message = reed_solomon_codec.encode(msg)
    #         self.sock.sendto(transmittable_message, socket.MSG_DONTWAIT, address + "_udp")
    #         # data_length = 0
    #         # start_message = "message_start_chunk_length %d" % len(transmittable_message)
    #         # self.sock.sendto(reed_solomon_codec.encode(start_message)[0], socket.MSG_DONTWAIT, address + "_udp")
    #         # for message in transmittable_message:
    #         #     data_length += self.sock.sendto(message, socket.MSG_DONTWAIT, address + "_udp")
    #         # return data_length
    #     except ConnectionRefusedError:
    #         self.lg.error(
    #             "simulator_stuff.sendto: the message {} has not been delivered because the destination {} left the team".format(
    #                 msg, address))
    #         raise
    #     except KeyboardInterrupt:
    #         self.lg.warning("simulator_stuff.sendto: send_packet {} to {}".format(msg, address))
    #         raise
    #     except FileNotFoundError:
    #         self.lg.error("simulator_stuff.sendto: {}".format(address + "_udp"))
    #         raise
    #     except BlockingIOError:
    #         raise

    # def recv_encoded(self, msg_length):
    #     msg = self.sock.recv(self.MAX_MSG_MENGTH)
    #     # start_message = str(reed_solomon_codec.decode(msg))
    #     # no_of_chunks = int(start_message.split(' ')[-1])
    #     #
    #     # message = None
    #     # for i in range(no_of_chunks):
    #     #     msg = self.sock.recv(self.MAX_MSG_MENGTH)
    #     #     decoded_msg = reed_solomon_codec.decode(msg)
    #     #     if message is None:
    #     #         message = decoded_msg
    #     #     else:
    #     #         message += decoded_msg
    #     #     self.lg.info("{} <= [{}] - {}".format(self.sock.getsockname(), decoded_msg, self.sock.getpeername()))
    #     # return message
    #
    # def recvfrom_encoded(self, max_msg_length):
    #     msg, sender = self.sock.recvfrom(self.MAX_MSG_MENGTH)
    #     start_message = str(reed_solomon_codec.decode(msg))
    #     no_of_chunks = int(start_message.split(' ')[-1])
    #
    #     message = None
    #     for i in range(no_of_chunks):
    #         msg, sender = self.sock.recv(self.MAX_MSG_MENGTH)
    #         decoded_msg = reed_solomon_codec.decode(msg)
    #         if message is None:
    #             message = decoded_msg
    #         else:
    #             message += decoded_msg
    #         sender = sender.replace("_tcp", "").replace("_udp", "")
    #         self.lg.info("{} <- [{}] - {}".format(self.sock.getsockname(), decoded_msg, sender))
    #     return message, sender
