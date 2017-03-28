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
import numpy as np
import random

class Simulator(object):

    P_IN = 0.8
    P_MoP = 0.5
    P_WIP = 0.5
    
    def __init__(self, set_of_rules, number_of_monitors, number_of_peers, drawing_log, number_of_rounds):
        self.set_of_rules = set_of_rules
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        self.drawing_log = drawing_log
        self.number_of_rounds = number_of_rounds
        
    def run_a_splitter(self):     
        splitter = Splitter_DBS()
        splitter.start()
        while splitter.alive:
            time.sleep(1)

    def run_a_peer(self, splitter_id, type, id):
        if type == "monitor":
            if self.set_of_rules == "dbs":
                peer = Monitor_DBS(id)
            elif self.set_of_rules == "cis":
                print("Monitors are TPs in CIS")
                peer = Monitor_STRPEDS(id)
        else:
            if self.set_of_rules == "dbs":
                peer = Peer_DBS(id)
            elif self.set_of_rules == "cis":
                peer = Peer_STRPEDS(id)
            
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
        self.net_labels={}
        self.color_map={'peer':'#A9BCF5', 'monitor':'#A9F5D0'}
        self.net_figure = plt.figure(1)

    def update_net(self,node, edge):
        plt.figure(1)
        if node:
            self.net_labels[node]=node
            if node[0] == "M":
                self.G.add_node(node, {'type':'monitor'})
            else:
                self.G.add_node(node, {'type':'peer'})
        else:
            self.G.add_edge(*edge)

        self.net_figure.clf()
        self.net_figure.suptitle("Overlay Network of the Team", size=16)
        nx.draw_circular(self.G, node_color=[self.color_map[self.G.node[node]['type']]for node in self.G], node_size=400, edge_color='#cccccc', labels=self.net_labels, font_size=10, font_weight='bold')
        self.net_figure.canvas.draw()

    def plot_team(self):
        self.team_figure, self.team_ax = plt.subplots()
        self.lineWIPs, = self.team_ax.plot([1,2], [10,10], color = '#A9BCF5', label="# WIPs", marker='o', ls='None' ,markeredgecolor='#A9BCF5', animated=True)
        self.lineMonitors, = self.team_ax.plot([1,2], [10,10], color = '#A9F5D0', label="# Monitor Peers", marker='o', ls='None', markeredgecolor='#A9F5D0', animated=True)
        self.team_figure.suptitle("Number of Peers in the Team", size=16)
        plt.legend(loc=2,numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers
        plt.axis([0, 2000, 0, total_peers])
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
        self.lineIN, = self.buffer_ax.plot([1]*2, [1]*2, color = '#A9BCF5', ls="None",label="IN", marker='o',markeredgecolor='#A9BCF5',animated=True)
        self.lineOUT, = self.buffer_ax.plot([1]*2, [1]*2, color = '#CCCCCC', ls="None", label="OUT", marker='o',markeredgecolor='#CCCCCC', animated=True)
        self.buffer_figure.suptitle("Buffer Status", size=16)
        plt.legend(loc=2,numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers
        plt.axis([0, total_peers+1, 0, 1024])
        self.buffer_order = {}
        self.buffer_index = 1
        self.buffer_labels = self.buffer_ax.get_xticks().tolist()
        print("XTICKS", self.buffer_labels)
        plt.grid()
        self.buffer_figure.canvas.draw()

    def update_buffer(self, node, buffer_shot):

        if self.buffer_order.get(node) == None:
            self.buffer_order[node] = self.buffer_index
            self.buffer_labels[self.buffer_index] = node
            self.buffer_ax.set_xticklabels(self.buffer_labels)
            self.buffer_index += 1

        buffer_out = [pos for pos, char in enumerate(buffer_shot) if char == "L"]
        self.lineOUT.set_xdata([self.buffer_order[node]]*len(buffer_out))
        self.lineOUT.set_ydata(buffer_out)
        self.buffer_ax.draw_artist(self.lineOUT)
            
        buffer_in = [pos for pos, char in enumerate(buffer_shot) if char == "C"]
        self.lineIN.set_xdata([self.buffer_order[node]]*len(buffer_in))
        self.lineIN.set_ydata(buffer_in)
        self.buffer_ax.draw_artist(self.lineIN)

        self.buffer_figure.canvas.blit(self.buffer_ax.bbox)       
        
    def store(self):
        drawing_log_file = open(self.drawing_log, "w", 1)
        queue = Common.SIMULATOR_FEEDBACK["DRAW"]
        m = queue.get()
        
        while m[0] != "Bye":
            drawing_log_file.write(";".join(map(str,m))+'\n')
            m= queue.get()

        drawing_log_file.write("Bye")
        drawing_log_file.close()

    def draw(self):
        drawing_log_file = open(self.drawing_log, "r")

        plt.ion()
        
        self.draw_net()
        self.plot_team()
        self.draw_buffer()
        
        line = drawing_log_file.readline()
        while line != "Bye":
            m = line.strip().split(";",3)
            
            if m[0] == "O":
                if m[1] == "Node":
                    self.update_net(m[2], None)
                else:
                    self.update_net(None, (m[2],m[3]))
            if m[0] == "T":
                try:
                    self.update_team(m[1],m[2],m[3])
                except:
                    #For visualization in real time (line is not fully written)
                    print("IndexError:", m, line)
                    pass

            if m[0] == "B":
                try:
                    self.update_buffer(m[1],m[2])
                except:
                    #For visualization in real time (line is not fully written)
                    print("IndexError:", m, line)
                    pass
                
            line = drawing_log_file.readline()

        #plt.ioff()
        #plt.show()

    def run(self):

        #Listen to the team for drawing
        Common.SIMULATOR_FEEDBACK["DRAW"] = Queue()
        Process(target=self.store).start()
        Process(target=self.draw).start()

        #Listen to the team for simulation life
        Common.SIMULATOR_FEEDBACK["STATUS"] = Queue()
                
        #create communication channels for the team and splitter
        Common.UDP_SOCKETS['S'] = Queue()
        Common.TCP_SOCKETS['S'] = Queue()

        for i in range(self.number_of_monitors):
            Common.UDP_SOCKETS["M"+str(i+1)] = Queue()

        for i in range(self.number_of_peers):
            Common.UDP_SOCKETS["P"+str(i+1)] = Queue()

        #run splitter
        Process(target=self.run_a_splitter).start()

        self.attended_monitors = 0
        self.attended_peers = 0

        #run monitor
        Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+1)]).start()
        self.attended_monitors += 1

        queue = Common.SIMULATOR_FEEDBACK["STATUS"]
        m = queue.get()
        while m[0] != "Bye":
            if (m[0] == "R"):
                r = random.randint(0,1)
                if r <= Simulator.P_IN:
                    self.addPeer()

                if m[1] == self.number_of_rounds:
                    Common.UDP_SOCKETS['S'].put(("SIM",(-1,"K")))
                                                
            m= queue.get()     

    def addPeer(self):
        probabilities = [Simulator.P_MoP,Simulator.P_WIP]
        option = np.where(np.random.multinomial(1,probabilities))[0][0]
        if option == 0:
            if self.attended_monitors < self.number_of_monitors:
                Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+1)]).start()
                self.attended_monitors += 1
        elif option == 1:
            if self.attended_peers < self.number_of_peers:
                Process(target=self.run_a_peer, args=["S", "peer", "P"+str(self.attended_peers+1)]).start()
                self.attended_peers += 1


        
if __name__ == "__main__":
    fire.Fire(Simulator)
    
