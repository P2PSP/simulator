#!/usr/bin/env python3

from core.splitter_dbs import Splitter_DBS
from core.splitter_strpeds import Splitter_STRPEDS
from core.splitter_sss import Splitter_SSS
from core.peer_dbs import Peer_DBS
from core.peer_strpeds import Peer_STRPEDS
from core.peer_sss import Peer_SSS
from core.peer_malicious import Peer_Malicious
from core.peer_malicious_sss import Peer_Malicious_SSS
from core.monitor_dbs import Monitor_DBS
from core.monitor_strpeds import Monitor_STRPEDS
from core.monitor_sss import Monitor_SSS
from core.common import Common
from multiprocessing import Process, Queue, Array, Manager
import time
import fire
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import sys
import numpy as np
import random
import ctypes
import platform

class Simulator(object):

    P_IN = 0.2
    P_MoP = 0.2
    P_WIP = 0.6
    P_MP = 0.2
    
    def __init__(self, set_of_rules, number_of_monitors, number_of_peers, drawing_log, number_of_rounds, number_of_malicious=0, gui = False):
        self.set_of_rules = set_of_rules
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        self.drawing_log = drawing_log
        self.number_of_rounds = number_of_rounds
        self.number_of_malicious = number_of_malicious
        self.current_round = 0
        self.gui = gui
        
    def get_team_size(self, n):  
        return 2**(n-1).bit_length()

    def get_buffer_size(self):
        team_size = self.get_team_size((self.number_of_monitors + self.number_of_peers + self.number_of_malicious)*2)
        if (team_size < 32):
            return 32
        else:
            return team_size
        
    def run_a_splitter(self):
        Common.BUFFER_SIZE = self.get_buffer_size()
        if self.set_of_rules == "dbs":
            splitter = Splitter_DBS()
        elif self.set_of_rules == "cis":
            splitter = Splitter_STRPEDS()
        elif self.set_of_rules == "cis-sss":
            splitter = Splitter_SSS()
        
        splitter.start()
        while splitter.alive:
            time.sleep(1)

    def run_a_peer(self, splitter_id, type, id):
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        chunks_before_leave = np.random.weibull(2) * (total_peers*(self.number_of_rounds-self.current_round))
        print(id,": alive till consuming",chunks_before_leave, "chunks")
        if type == "monitor":
            if self.set_of_rules == "dbs":
                peer = Monitor_DBS(id)
            elif self.set_of_rules == "cis":
                print("Monitors are TPs in CIS")
                peer = Monitor_STRPEDS(id)
            elif self.set_of_rules == "cis-sss":
                print("Monitors are TPs in CIS")
                peer = Monitor_SSS(id)
        elif type == "malicious":
            if self.set_of_rules == "cis":
                peer = Peer_Malicious(id)
            elif self.set_of_rules == "cis-sss":
                peer = Peer_Malicious_SSS(id)
            else:
                print("Malicious peers are only compatible with CIS")
        else:
            if self.set_of_rules == "dbs":
                peer = Peer_DBS(id)
            elif self.set_of_rules == "cis":
                peer = Peer_STRPEDS(id)
            elif self.set_of_rules == "cis-sss":
                peer = Peer_SSS(id)
            
        peer.set_splitter(splitter_id)
        peer.connect_to_the_splitter()
        peer.receive_buffer_size()
        peer.receive_the_number_of_peers()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        peer.buffer_data()
        peer.start()
          
        while not peer.ready_to_leave_the_team:
            if type != "malicious" and peer.number_of_chunks_consumed >= chunks_before_leave and peer.player_alive:
                print(id, "reached the number of chunks consumed before leave", peer.number_of_chunks_consumed)
                peer.player_alive = False
                
        print(id, "left the team")
            
    def draw_net(self):
        self.G = nx.Graph()
        self.net_labels={}
        self.color_map={'peer':'#A9BCF5', 'monitor':'#A9F5D0', 'malicious':'#F78181'}
        self.net_figure = plt.figure(1)

    def update_net(self, node, edge, direction):
        plt.figure(1)
        #print("Update net", node, edge, direction)
        if node:
            self.net_labels[node]=node
            if node[0] == "M" and node[1] == "P":
                if direction == "IN":
                    self.G.add_node(node, behaviour='malicious')
                else:
                    print(node,"removed from graph (MP)")
                    self.G.remove_node(node)
                    del self.net_labels[node]
            elif node[0] == "M":
                if direction == "IN":
                    self.G.add_node(node, behaviour='monitor')
                else:
                    self.G.remove_node(node)
                    del self.net_labels[node]
            else:
                if direction == "IN":
                    self.G.add_node(node, behaviour='peer')
                else:
                    self.G.remove_node(node)
                    del self.net_labels[node]
        else:
            if edge[0] and edge[1] in self.G.nodes():
                if direction == "IN":
                    self.G.add_edge(*edge, color='#000000')
                else:
                    self.G.add_edge(*edge, color='r')

        self.net_figure.clf()
        edges = self.G.edges()
        edge_color = [self.G[u][v]['color'] for u,v in edges]
        #print("NODOS", self.G.nodes())
        #for node in self.G.nodes():
        #    print("NODOS", self.G.node[node])
        node_color = [self.color_map[self.G.node[node]['behaviour']]for node in self.G]
        self.net_figure.suptitle("Overlay Network of the Team", size=16)
        nx.draw_circular(self.G, node_color=node_color, node_size=400, edge_color=edge_color, labels=self.net_labels, font_size=10, font_weight='bold')
        self.net_figure.canvas.draw()

    def plot_team(self):
        self.team_figure, self.team_ax = plt.subplots()
        self.lineWIPs, = self.team_ax.plot([1,2], [10,10], color = '#A9BCF5', label="# WIPs", marker='o', ls='None' ,markeredgecolor='#A9BCF5', animated=True)
        self.lineMonitors, = self.team_ax.plot([1,2], [10,10], color = '#A9F5D0', label="# Monitor Peers", marker='o', ls='None', markeredgecolor='#A9F5D0', animated=True)
        self.lineMPs, = self.team_ax.plot([1,2], [10,10], color = '#DF0101', label="# Malicious Peers", marker='o', ls='None', markeredgecolor='#DF0101', animated=True)
        self.team_figure.suptitle("Number of Peers in the Team", size=16)
        plt.legend(loc=2,numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        plt.axis([0, self.number_of_rounds, 0, total_peers])
        self.team_figure.canvas.draw()
                
    def update_team(self, node, quantity, n_round):
        
        if node == "M":
            self.lineMonitors.set_xdata(n_round)
            self.lineMonitors.set_ydata(quantity)
            self.team_ax.draw_artist(self.lineMonitors)
        elif node == "P":
            self.lineWIPs.set_xdata(n_round)
            self.lineWIPs.set_ydata(quantity)
            self.team_ax.draw_artist(self.lineWIPs)
        else:
            self.lineMPs.set_xdata(n_round)
            self.lineMPs.set_ydata(quantity)
            self.team_ax.draw_artist(self.lineMPs)

        self.team_figure.canvas.blit(self.team_ax.bbox)

        
    def draw_buffer(self):
        self.buffer_figure, self.buffer_ax = plt.subplots()
        self.lineIN, = self.buffer_ax.plot([1]*2, [1]*2, color = '#000000', ls="None",label="IN", marker='o',markeredgecolor='#000000',animated=True)
        self.lineOUT, = self.buffer_ax.plot([1]*2, [1]*2, color = '#CCCCCC', ls="None", label="OUT", marker='o',markeredgecolor='#CCCCCC', animated=True)
        self.buffer_figure.suptitle("Buffer Status", size=16)
        plt.legend(loc=2,numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        self.buffer_colors = cm.rainbow(np.linspace(0, 1, total_peers))
        plt.axis([0, total_peers+1, 0, self.get_team_size(total_peers*2)])
        plt.xticks(range(0, total_peers+1,1))
        self.buffer_order = {}
        self.buffer_index = 1
        self.buffer_labels = self.buffer_ax.get_xticks().tolist()
        plt.grid()
        self.buffer_figure.canvas.draw()

    def update_buffer_round(self, number_of_round):
        self.buffer_figure.suptitle("Buffer Status "+number_of_round, size=16)

    def update_buffer(self, node, buffer_shot, senders_shot):
        
        if self.buffer_order.get(node) == None:
            self.buffer_order[node] = self.buffer_index
            self.buffer_labels[self.buffer_index] = node
            self.buffer_ax.set_xticklabels(self.buffer_labels)
            self.buffer_ax.get_xticklabels()[self.buffer_index].set_color(self.buffer_colors[(self.buffer_index-1)])
            self.buffer_index += 1

        buffer_out = [pos for pos, char in enumerate(buffer_shot) if char == "L"]
        self.lineOUT.set_xdata([self.buffer_order[node]]*len(buffer_out))
        self.lineOUT.set_ydata(buffer_out)
        self.buffer_ax.draw_artist(self.lineOUT)
            
        buffer_in = [pos for pos, char in enumerate(buffer_shot) if char == "C"]
        sender_list = senders_shot.split(":")
        self.lineIN.set_xdata([self.buffer_order[node]]*len(buffer_in))
        for pos in buffer_in:
            sender_node = sender_list[pos]
            if ( sender_node != "S"):
                color_position = self.buffer_order[sender_node]-1
                self.lineIN.set_color(self.buffer_colors[color_position])
            else:
                self.lineIN.set_color("#000000")
            self.lineIN.set_ydata(pos)
            self.buffer_ax.draw_artist(self.lineIN)

        self.buffer_figure.canvas.blit(self.buffer_ax.bbox)

    def plot_clr(self):
        self.clrs_per_round = []
        self.clr_figure, self.clr_ax = plt.subplots()
        self.lineCLR, = self.clr_ax.plot([1,2], [10,10], color = '#000000', label="CLR", marker='o', ls='None' ,markeredgecolor='#000000', animated=True)
        self.clr_figure.suptitle("Chunk Loss Ratio", size=16)
        plt.legend(loc=2,numpoints=1)
        plt.axis([0, self.number_of_rounds, 0, 1])
        self.clr_figure.canvas.draw()
                
    def update_clrs(self, peer, clr):
        if peer[:2] != "MP":
            self.clrs_per_round.append(clr)

    def update_clr_plot(self, n_round):
         if len(self.clrs_per_round) > 0:
             self.lineCLR.set_xdata(n_round)
             self.lineCLR.set_ydata(np.mean(self.clrs_per_round))
             self.clr_ax.draw_artist(self.lineCLR)
             self.clr_figure.canvas.blit(self.clr_ax.bbox)
             self.clrs_per_round = []
        
    def store(self):
        drawing_log_file = open(self.drawing_log, "w", 1)

        #Configuration in the first line
        m = ["C",self.number_of_monitors, self.number_of_peers, self.number_of_malicious, self.number_of_rounds, self.set_of_rules]
        drawing_log_file.write(";".join(map(str,m))+'\n')
    
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
        self.plot_clr()
        time.sleep(1)
        line = drawing_log_file.readline()
        while line != "Bye":
            m = line.strip().split(";",4)
            if m[0] == "O":
                if m[1] == "Node":
                    if m[2] == "IN":
                        self.update_net(m[3], None, "IN")
                    else:
                        self.update_net(m[3], None, "OUT")
                else:
                    if m[2] == "IN":
                        self.update_net(None, (m[3],m[4]), "IN")
                    else:
                        self.update_net(None, (m[3],m[4]), "OUT")
                        
            if m[0] == "T":
                try:
                    self.update_team(m[1],m[2],m[3])
                except:
                    #For visualization in real time (line is not fully written)
                    print("IndexError:", m, line)
                    pass
                
            if m[0] == "B":
                try:
                    self.update_buffer(m[1], m[2], m[3])
                    buffer_shot = None
                except Exception as inst:
                    #For visualization in real time (line is not fully written)
                    print("IndexError:", m, line)
                    print(inst.args)
                    pass

            if m[0] == "CLR":
                self.update_clrs(m[1],float(m[2]))

            if m[0] == "R":
                self.update_clr_plot(m[1])
                #self.update_buffer_round(m[1])
                
            line = drawing_log_file.readline()

        #plt.ioff()
        #plt.show()

    def run(self):
        print("platform.system() = ", platform.system())
        if platform.system() == 'Linux':
            plt.switch_backend("TkAgg")
        elif platform.system() == 'Darwin':
            plt.switch_backend("macosx")
        plt.style.use("seaborn-white")
        
        #Listen to the team for drawing
        Common.SIMULATOR_FEEDBACK["DRAW"] = Queue()
        Process(target=self.store).start()
        
        if self.gui == True:
            Process(target=self.draw).start()

        #Listen to the team for simulation life
        Common.SIMULATOR_FEEDBACK["STATUS"] = Queue()
                
        #create communication channels for the team and splitter
        Common.UDP_SOCKETS['S'] = Queue()
        Common.TCP_SOCKETS['S'] = Queue()

        #create shared list for CIS set of rules (only when cis is choosen?)
        manager = Manager()
        Common.SHARED_LIST["malicious"] = manager.list()
        Common.SHARED_LIST["regular"] = manager.list()
        Common.SHARED_LIST["attacked"] = manager.list()

        for i in range(self.number_of_monitors):
            Common.UDP_SOCKETS["M"+str(i+1)] = Queue()

        for i in range(self.number_of_peers):
            Common.UDP_SOCKETS["P"+str(i+1)] = Queue()

        for i in range(self.number_of_malicious):
            Common.UDP_SOCKETS["MP"+str(i+1)] = Queue()

        #run splitter
        Process(target=self.run_a_splitter).start()

        self.attended_monitors = 0
        self.attended_peers = 0
        self.attended_mps = 0

        #run a monitor
        Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+1)]).start()
        self.attended_monitors += 1

        queue = Common.SIMULATOR_FEEDBACK["STATUS"]
        m = queue.get()
        while m[0] != "Bye":
            if (m[0] == "R"):
                self.current_round = m[1]
                r = np.random.uniform(0,1)
                if r <= Simulator.P_IN:
                    self.addPeer()

                if self.current_round == self.number_of_rounds:
                    Common.UDP_SOCKETS['S'].put(("SIM",(-1,"K")))
                                                
            m= queue.get()     

    def addPeer(self):
        probabilities = [Simulator.P_MoP, Simulator.P_WIP, Simulator.P_MP]
        option = np.where(np.random.multinomial(1,probabilities))[0][0]
        if option == 0:
            if self.attended_monitors < self.number_of_monitors:
                Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+1)]).start()
                self.attended_monitors += 1
        elif option == 1:
            if self.attended_peers < self.number_of_peers:
                Process(target=self.run_a_peer, args=["S", "peer", "P"+str(self.attended_peers+1)]).start()
                self.attended_peers += 1
        elif option == 2:
            if self.attended_mps < self.number_of_malicious:
                Process(target=self.run_a_peer, args=["S", "malicious", "MP"+str(self.attended_mps+1)]).start()
                self.attended_mps += 1

        
if __name__ == "__main__":
    fire.Fire(Simulator)
    
