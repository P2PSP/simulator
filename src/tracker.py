#!/usr/bin/env python

import socket
import struct
from threading import Thread


class Tracker:

    def run(self):
        IM_NEW_SPLITTER = 0
        SEND_SPLITTERS = 1
        channel_to_splitters = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", 8888))
        sock.listen(1)
        while True:
            connection, _from = sock.accept()
            message = connection.recv(1024)
            channel_bytes = len(message) - 4
            message_format = "i" + str(channel_bytes) + "s"
            message = struct.unpack(message_format, message)
            command = message[0]
            channel = message[1]
            if command == IM_NEW_SPLITTER:
                if channel_to_splitters[channel] == None:
                    channel_to_splitters[channel] = {}
                channel_to_splitters[channel].append(_from)
                print("splitter " + _from + " for channel " + channel + " added")
            elif command == SEND_SPLITTERS:
                connection.send(channel_to_splitters[channel])
                print("request " + channel + " from " + _from)
            else:
                print("Unexpexted message format")
            connection.close()

    def main(self):
        Thread(target=self.run).start()


if __name__ == "__main__":
    t = Tracker()
    t.main()
