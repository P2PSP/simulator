import socket
import queue

class Peer_STS():

    def time_connection(self, server, queue):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(server)
            print("Conncted to " +  str(server))
            if queue.empty:
                queue.put(server)
            s.close()
        except:
            print(str(server) + "does not respond")

    def connect_closest_splitter(self, splitters):
        q = queue.Queue()
        for s in splitters:
            


    def salute_the_load_balancer(self, balancer, channel)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(balancer)
        s.send("NEW " + channel)
        s.close()

    def get_splitters_list(self, tracker, channel):
        s.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(tracker)
        s.send("GET " + channel)
        splitters = s.recv(1024)
        s.close()

    def main(self, balancer, tracker, channel):
        salute_the_load_balancer(balancer, channel)
        splitters = get_splitters_list(tracker, channel)
        self.connected_splitter = connect_closest_splitter(splitters)
        
