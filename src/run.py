from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.splitter_dbs import Splitter_DBS
from core.common import Common
from threading import Thread
from multiprocessing import Process, Queue
import time
import networkx as nx
import matplotlib.pyplot as plt

class Simulator:

    def __init__(self, number_of_monitors, number_of_peers):
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        
    def run_a_splitter(self):     
        splitter = Splitter_DBS()
        splitter.start()
        while splitter.alive:
            time.sleep(1)
            print("Splitter's list of peers:", ', '.join(str(p) for p in splitter.peer_list))

    def run_a_peer(self, splitter_id, type, id):
        if type == "monitor":
            peer = Monitor_DBS(id)
        else:
            peer = Peer_DBS(id)
            
        peer.set_splitter(splitter_id)
        peer.connect_to_the_splitter()
        peer.receive_the_number_of_peers()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        peer.buffer_data()
        peer.start()

        while peer.player_alive:
            pass
            
    def run(self):
        Common.SIMULATOR_FEEDBACK["TEAM"] = Queue()
        Thread(target=self.draw_net).start()
        
        Common.UDP_SOCKETS['S'] = Queue()
        Common.TCP_SOCKETS['S'] = Queue()

        for i in range(self.number_of_monitors):
            Common.UDP_SOCKETS["M"+str(i+1)] = Queue()

        for i in range(self.number_of_peers):
            Common.UDP_SOCKETS["P"+str(i+1)] = Queue()


        Process(target=self.run_a_splitter).start()

            
        for i in range(self.number_of_monitors):
            time.sleep(0.5)
            Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(i+1)]).start()
        
        for i in range(self.number_of_peers):
            time.sleep(1)
            Process(target=self.run_a_peer, args=["S", "peer", "P"+str(i+1)]).start()

    def draw_net(self):
        G = nx.Graph()

        team  = Common.SIMULATOR_FEEDBACK["TEAM"]

        plt.ion()
        
        m = team.get()
        while m[0] != "":
            if m[0] == "Node":
                G.add_node(m[1])
            else:
                #m[0] == "Edge":
                G.add_edge(*m[1])
                 
            plt.clf()
            nx.draw_circular(G)
            plt.pause(0.001)
            m = team.get()
            
if __name__ == "__main__":
    app = Simulator(1,5)
    app.run()
    
