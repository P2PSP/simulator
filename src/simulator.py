#!/usr/bin/env python3

from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.splitter_dbs import Splitter_DBS
from core.common import Common
from multiprocessing import Process, Queue
import time
import fire
import networkx as nx
import matplotlib.pyplot as plt
import sys

class Simulator(object):

    def __init__(self, number_of_monitors, number_of_peers, draw_filename):
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        self.draw_filename = draw_filename
        
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
            
    def draw_net(self):
        self.G = nx.Graph()
        self.labels={}
        self.color_map={'peer':'#A9BCF5', 'monitor':'#A9F5D0'}
        self.net_figure = plt.figure(1)

    def update_net(self,node, edge):
        plt.figure(1)
        if node:
            self.labels[node]=node
            if node[0] == "M":
                self.G.add_node(node, {'type':'monitor'})
            else:
                self.G.add_node(node, {'type':'peer'})
        else:
            self.G.add_edge(*edge)

        self.net_figure.clf()
        self.net_figure.suptitle("Overlay Network of the Team", size=16)
        nx.draw_circular(self.G, node_color=[self.color_map[self.G.node[node]['type']]for node in self.G], node_size=400, edge_color='#cccccc', labels=self.labels, font_size=10, font_weight='bold')
        self.net_figure.canvas.draw()

    def plot_team(self):
        self.team_figure, self.team_ax = plt.subplots()
        self.lineWIPs, = self.team_ax.plot(1, 1, color = '#A9BCF5', label="# Monitor Peers", marker='o',markeredgecolor='#A9BCF5', animated=True)
        self.lineMonitors, = self.team_ax.plot(1, 1, color = '#A9F5D0', label="# WIPs", marker='o',markeredgecolor='#A9F5D0', animated=True)
        self.team_figure.suptitle("Number of Peers in the Team", size=16)
        plt.legend(loc=2)
        plt.axis([0, 2000, 0, 4])
        self.team_figure.canvas.draw()
                
    def update_team(self, node, quantity, n_round):
        
        if node == "M":
            self.lineMonitors.set_xdata(n_round)
            self.lineMonitors.set_ydata(quantity)
            self.team_ax.draw_artist(self.lineMonitors)
        else:
            self.lineWIPs.set_xdata(n_round)
            self.lineWIPs.set_ydata(quantity)
            self.team_ax.draw_artist(self.lineWIPs)

        self.team_figure.canvas.blit(self.team_ax.bbox)

        
    def draw_buffer(self):
        self.buffer_figure, self.buffer_ax = plt.subplots()
        self.lineIN, = self.buffer_ax.plot(1, 1, color = '#A9BCF5', ls="None",label="IN", marker='o',markeredgecolor='#A9BCF5',animated=True)
        self.lineOUT, = self.buffer_ax.plot(1, 1, color = '#CCCCCC', ls="None", label="OUT", marker='o',markeredgecolor='#CCCCCC', animated=True)
        self.buffer_figure.suptitle("Buffer Status", size=16)
        plt.legend(loc=2)
        total_peers = self.number_of_monitors + self.number_of_peers
        plt.axis([0, total_peers+1, 0, 1024])
        self.buffer_order = {}
        self.buffer_index = 1
        #plt.xticks(x,labels)
        self.buffer_figure.canvas.draw()

    def update_buffer(self, node, buffer_shot):

        if self.buffer_order.get(node) == None:
            self.buffer_order[node] = self.buffer_index
            self.buffer_index += 1
        
        buffer_in = [pos for pos, char in enumerate(buffer_shot) if char == "C"]
        self.lineIN.set_xdata([self.buffer_order[node]]*len(buffer_in))
        self.lineIN.set_ydata(buffer_in)
        self.buffer_ax.draw_artist(self.lineIN)

        buffer_out = [pos for pos, char in enumerate(buffer_shot) if char == "L"]
        self.lineOUT.set_xdata([self.buffer_order[node]]*len(buffer_out))
        self.lineOUT.set_ydata(buffer_out)
        self.buffer_ax.draw_artist(self.lineOUT)

        self.buffer_figure.canvas.blit(self.buffer_ax.bbox)       
        
    def store(self):
        draw_file = open(self.draw_filename, "w", 1)
        queue = Common.SIMULATOR_FEEDBACK["DRAW"]
        m = queue.get()
        
        while m[0] != "Bye":
            draw_file.write(";".join(map(str,m))+"\n")
            m= queue.get()

        draw_file.close()

    def draw(self, draw_file):
        draw_file = open(self.draw_filename, "r")

        plt.ion()

        self.draw_net()
        self.plot_team()
        self.draw_buffer()
        
        line = draw_file.readline()
        while line != "Bye":
            m = line.strip().split(";",3)
            
            if m[0] == "O":
                if m[1] == "Node":
                    self.update_net(m[2], None)
                else:
                    self.update_net(None, (m[2],m[3]))
            if m[0] == "T":
                self.update_team(m[1],m[2],m[3])
            if m[0] == "B":
                try:
                    self.update_buffer(m[1],m[2])
                except:
                    e = sys.exc_info()[0]
                    print("INDEX-ERROR", e)
                    sys.exit(1)
                
            line = draw_file.readline()
            
        plt.ioff()
        plt.show()

    def run(self):

        #Listen to the team for drawing
        Common.SIMULATOR_FEEDBACK["DRAW"] = Queue()
        Process(target=self.store).start()

        Process(target=self.draw, args=[self.draw_filename]).start()
        
        #listen to the team for uptating overlay graph
        #Common.SIMULATOR_FEEDBACK["OVERLAY"] = Queue(100)
        #Process(target=self.draw_net).start()

        #listen to the splitter for uptating team plot
        #Common.SIMULATOR_FEEDBACK["TEAM"] = Queue(100)
        #Process(target=self.plot_team).start()

        #listen to the team for uptating buffer graph
        #Common.SIMULATOR_FEEDBACK["BUFFER"] = Queue(100)
        #Process(target=self.draw_buffer2).start()
        
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
            time.sleep(1)
            Process(target=self.run_a_peer, args=["S", "peer", "P"+str(i+1)]).start()

         
if __name__ == "__main__":
    fire.Fire(Simulator)
    
