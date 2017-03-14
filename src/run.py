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
        #listen to the team for uptating graph
        Common.SIMULATOR_FEEDBACK["TEAM"] = Queue()
        Thread(target=self.draw_net).start()

        #create communication channels for the team and splitter
        Common.UDP_SOCKETS['S'] = Queue()
        Common.TCP_SOCKETS['S'] = Queue()

        for i in range(self.number_of_monitors):
            Common.UDP_SOCKETS["M"+str(i+1)] = Queue()

        for i in range(self.number_of_peers):
            Common.UDP_SOCKETS["P"+str(i+1)] = Queue()

        #run splitter
        Process(target=self.run_a_splitter).start()

        #run monitor peers
        for i in range(self.number_of_monitors):
            time.sleep(0.5)
            Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(i+1)]).start()
            
        #run regular peers
        for i in range(self.number_of_peers):
            time.sleep(0.5)
            Process(target=self.run_a_peer, args=["S", "peer", "P"+str(i+1)]).start()

            
    def draw_net(self):
        G = nx.Graph()

        team  = Common.SIMULATOR_FEEDBACK["TEAM"]

        plt.ion()
         
        labels={}
        color_map={'peer':'#A9BCF5', 'monitor':'#A9F5D0'}
        
        m = team.get()
        while m[0] != "Bye":
            if m[0] == "Node":
                labels[m[1]]=m[1]
                if m[1][0] == "P":
                    G.add_node(m[1], {'type':'peer'})
                else:
                    G.add_node(m[1], {'type':'monitor'})
            else:
                #m[0] == "Edge":
                G.add_edge(*m[1])

            plt.clf()
            nx.draw_circular(G, node_color=[color_map[G.node[node]['type']]for node in G], node_size=400, edge_color='#cccccc', labels=labels, font_size=10, font_weight='bold')
            plt.pause(0.05)

            m = team.get()
         
if __name__ == "__main__":
    app = Simulator(1,5)
    app.run()
    
