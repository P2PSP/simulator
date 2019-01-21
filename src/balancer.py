#!/usr/bin/env python

# TODO: connect with icecast servers and retrieve the load

import queue
import socket
import threading

import flask


class Balancer:

    def time_connection(self, server, queue):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(server)
            print("Conncted to " + str(server))
            if queue.empty:
                queue.put(server)
            s.close()
        except:
            print(str(server) + "does not respond")

    app = flask.Flask(__name__)

    @app.route("/<mountpoint>")
    def get_mountpoint(self, mountpoint):
        q = queue.Queue()
        data = open("servers.txt")
        for line in data:
            (host, port) = line.split(":")
            port = int(port)
            server = (host, port)
            print("Processing server:" + str(server))
            threading.Thread(target=self.time_connection, args=(server, q)).start()

        tmp = q.get()
        selected_server = tmp[0] + ":" + str(tmp[1])
        URL = "http://" + selected_server + "/" + str(mountpoint)
        print("Selected server: " + URL)
        return flask.redirect(URL, code=302)

    def run(self):
        app.run(host="0.0.0.0", port=7777)
        # The rest of the logic would be:
        # listen to HTTP GETs and reply with the unloadest server.
        # listen to

    def main(self):
        Thread(target=self.run).start()


if __name__ == "__main__":
    t = Tracker()
    t.main()
