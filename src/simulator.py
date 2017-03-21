#!/usr/bin/env python3

from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.splitter_dbs import Splitter_DBS
from core.common import Common
from threading import Thread
from multiprocessing import Process, Queue
import time
import fire
import networkx as nx
import matplotlib.pyplot as plt
from collections import OrderedDict

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
        queue = Common.SIMULATOR_FEEDBACK["BUFFER"]
        plt.ion()

        buffers = {}
        lines = {}
        index = {}
        labels = []
        
        fig, ax = plt.subplots()
                
        plt.suptitle("Buffer Status", size=16)
        plt.axis([0, 21, 0, 1024])
        x = range(21)
        labels.append("")
        fig.canvas.draw()
        bk = fig.canvas.copy_from_bbox(ax.bbox)
        j = 1
        i = 0
        m = queue.get()
        while m[0] != "Bye":            
            if m[0] == "IN":
                
                if index.get(m[1]) == None:
                    lineIN, = ax.plot(j, 0, color = '#A9F5D0', marker='o', markeredgecolor='#A9F5D0', animated=True)
                    lineOUT, = ax.plot(j, 0, color = '#CCCCCC', marker='o',markeredgecolor='#CCCCCC', animated=True)
                    lines[m[1]] = (lineIN, lineOUT)
                    index[m[1]] = j
                    labels.append(m[1])
                    plt.xticks(x,labels)
                    fig.canvas.blit(ax.bbox)
                    j += 1

                fig.canvas.restore_region(bk)
                lines[m[1]][0].set_xdata(index[m[1]])
                lines[m[1]][0].set_ydata(m[2])
                ax.draw_artist(lines[m[1]][0])
                bk = fig.canvas.copy_from_bbox(ax.bbox)
                #fig.canvas.blit(ax.bbox)
            elif m[0] == "OUT":
                fig.canvas.restore_region(bk)
                lines[m[1]][1].set_xdata(index[m[1]])
                lines[m[1]][1].set_ydata(m[2])
                ax.draw_artist(lines[m[1]][1])
                bk = fig.canvas.copy_from_bbox(ax.bbox)
                #fig.canvas.blit(ax.bbox)
            else:
                print("Error: unknown message")

            #plt.clf()
            '''
            i = 1
            for k,v in buffers.items():
                fig.canvas.restore_region(bk)
                lines[k].set_xdata(i)
                lines[k].set_ydata(v[-1])
                ax.draw_artist(lines[k])
                bk = fig.canvas.copy_from_bbox(ax.bbox)

                i += 1
                #plt.pause(0.001)
                #fig.canvas.draw()
            '''
            #fig.canvas.blit(ax.bbox)

            if(i%20 ==0):
                fig.canvas.blit(ax.bbox)
            i+=1
            m = queue.get()

        plt.ioff()
        plt.show()

    def draw_buffer2(self):
        total_peers = self.number_of_monitors + self.number_of_peers
        queue = Common.SIMULATOR_FEEDBACK["BUFFER"]
        plt.ion()

        buffersIN = {}
        buffersOUT = {}
        lines = {}
        index = {}
        labels = []

        for i in range(self.number_of_monitors):
            buffersIN.setdefault("M"+str(i+1),[]).append(0)
            buffersOUT.setdefault("M"+str(i+1),[]).append(0)

        for i in range(self.number_of_peers):
            buffersIN.setdefault("P"+str(i+1),[]).append(0)
            buffersOUT.setdefault("P"+str(i+1),[]).append(0)
        
        fig, ax = plt.subplots()
                
        plt.suptitle("Buffer Status", size=16)
        plt.axis([0, total_peers+1, 0, 1024])
        x = range(1,total_peers+1)
        labels.append("")
        fig.canvas.draw()
        bk = fig.canvas.copy_from_bbox(ax.bbox)
        vueltas = 0     

        lineIN, = ax.plot(x, [0]*total_peers, color = '#A9F5D0', ls='None', marker='o',markeredgecolor='#A9F5D0', animated=True)
        lineOUT, = ax.plot(x, [0]*total_peers, color = '#CCCCCC', ls='None', marker='o',markeredgecolor='#CCCCCC', animated=True)
        
        plt.xticks(x,labels)
        j = 1
        m = queue.get()
        while m[0] != "Bye":
            print("SIZE queue", queue.qsize())
            
            if m[0] == "IN":
                #fig.canvas.restore_region(bk)
                
                if index.get(m[1]) == None:
                    index[m[1]] = j
                    j += 1
                
                #buffersIN.setdefault(m[1],[]).append(m[2])
                #labels.append(m[1])
                #lst = list(buffersIN.values())
                #lineIN.set_ydata(list(zip(*lst))[-1])
                lineIN.set_xdata(index[m[1]])
                lineIN.set_ydata(m[2])
                ax.draw_artist(lineIN)
                #bk = fig.canvas.copy_from_bbox(ax.bbox)
                #fig.canvas.blit(ax.bbox)
            elif m[0] == "OUT":
                if index.get(m[1]) == None:
                    index[m[1]] = j
                    j += 1
                #fig.canvas.restore_region(bk)
                #buffersOUT.setdefault(m[1],[]).append(m[2])
                #lst = list(buffersOUT.values())
                #lineOUT.set_ydata(list(zip(*lst))[-1])
                lineOUT.set_xdata(index[m[1]])
                lineOUT.set_ydata(m[2])
                ax.draw_artist(lineOUT)
                #bk = fig.canvas.copy_from_bbox(ax.bbox)
                #fig.canvas.blit(ax.bbox)

            else:
                print("Error: unknown message")

            if (vueltas % 20 == 0):
                fig.canvas.blit(ax.bbox)

            vueltas +=  1
            
            m = queue.get()

        plt.ioff()
        plt.show()


        
    def store(self):
        queue = Common.SIMULATOR_FEEDBACK["DRAW"]
        m = queue.get()
        draw_file = open(self.draw_filename, "w", 1)
        
        while m[0] != "Bye":
            draw_file.write(";".join(map(str,m))+"\n")
            m= queue.get()

        draw_file.close()

    def draw(self, draw_file):
        draw_file = open(self.draw_filename, "r")

        plt.ion()

        self.draw_net()
        self.plot_team()
        
        line = draw_file.readline()
        while line != "Bye":
            m = line.strip().split(";",3)
            if m[0] == "O":
                if m[1] == "Node":
                    pass
                    self.update_net(m[2], None)
                else:
                    pass
                    self.update_net(None, (m[2],m[3]))
            if m[0] == "T":
                self.update_team(m[1],m[2],m[3])
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
    
