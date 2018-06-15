#!/usr/bin/env python3

import time
import fire
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import logging

class Play():
    
    def __init__(self, drawing_log):
        self.drawing_log = drawing_log
        self.Type = {}

    def get_team_size(self, n):
        return 2 ** (n - 1).bit_length()
        
    def get_buffer_size(self):
        team_size = self.get_team_size((self.number_of_monitors + self.number_of_peers + self.number_of_malicious) * 8)
        if (team_size < 32):
            return 32
        else:
            return team_size
        
    def draw_net(self):
        self.G = nx.Graph()
        self.net_labels = {}
        self.color_map = {'peer': '#A9BCF5', 'monitor': '#A9F5D0', 'malicious': '#F78181'}
        self.net_figure = plt.figure(1)

    def update_net(self, node, edge, direction):
        plt.figure(1)
        # self.lg.info("Update net", node, edge, direction)
        if node:
            self.net_labels[node] = node
            if node in self.Type and self.Type[node]=="MP":
                if direction == "IN":
                    self.G.add_node(node, behaviour='malicious')
                else:
                    self.lg.info("simulator: {} removed from graph (MP)".format(node))
                    self.G.remove_node(node)
                    del self.net_labels[node]
            elif node in self.Type and self.Type[node]== "M":
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
            if edge[0] in self.G.nodes() and edge[1] in self.G.nodes():
                if direction == "IN":
                    self.G.add_edge(*edge, color='#000000')
                else:
                    self.G.add_edge(*edge, color='r')

        self.net_figure.clf()
        edges = self.G.edges()
        edge_color = [self.G[u][v]['color'] for u, v in edges]
        node_color = [self.color_map[self.G.node[node]['behaviour']] for node in self.G]
        self.net_figure.suptitle("Overlay Network of the Team", size=16)
        nx.draw_circular(self.G, node_color=node_color, node_size=400, edge_color=edge_color, labels=self.net_labels,
                         font_size=10, font_weight='bold')
        self.net_figure.canvas.draw()

    def plot_team(self):
        self.team_figure, self.team_ax = plt.subplots()
        self.lineWIPs, = self.team_ax.plot([1, 2], [10, 10], color='#A9BCF5', label="# WIPs", marker='o', ls='None',
                                           markeredgecolor='#A9BCF5', animated=True)
        self.lineMonitors, = self.team_ax.plot([1, 2], [10, 10], color='#A9F5D0', label="# Monitor Peers", marker='o',
                                               ls='None', markeredgecolor='#A9F5D0', animated=True)
        self.lineMPs, = self.team_ax.plot([1, 2], [10, 10], color='#DF0101', label="# Malicious Peers", marker='o',
                                          ls='None', markeredgecolor='#DF0101', animated=True)
        self.team_figure.suptitle("Number of Peers in the Team", size=16)
        plt.legend(loc=2, numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        plt.axis([0, self.number_of_rounds, 0, total_peers])
        self.team_figure.canvas.draw()

    def update_team(self, node, quantity, n_round):
        if node == "M":
            self.lineMonitors.set_xdata(float(n_round))
            self.lineMonitors.set_ydata(float(quantity))
            self.team_ax.draw_artist(self.lineMonitors)
        elif node == "P":
            self.lineWIPs.set_xdata(float(n_round))
            self.lineWIPs.set_ydata(float(quantity))
            self.team_ax.draw_artist(self.lineWIPs)
        else:
            self.lineMPs.set_xdata(float(n_round))
            self.lineMPs.set_ydata(float(quantity))
            self.team_ax.draw_artist(self.lineMPs)

        self.team_figure.canvas.blit(self.team_ax.bbox)

    def draw_buffer(self):
        self.buffer_figure, self.buffer_ax = plt.subplots()
        self.lineIN, = self.buffer_ax.plot([1] * 2, [1] * 2, color='#000000', ls="None", label="IN", marker='o',
                                           animated=True)
        self.lineOUT, = self.buffer_ax.plot([1] * 2, [1] * 2, color='#CCCCCC', ls="None", label="OUT", marker='o',
                                            animated=True)
        self.buffer_figure.suptitle("Buffer Status", size=16)
        plt.legend(loc=2, numpoints=1)
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        self.buffer_colors = cm.rainbow(np.linspace(0, 1, total_peers))
        plt.axis([0, total_peers + 1, 0, self.get_buffer_size()])
        plt.xticks(range(0, total_peers + 1, 1))
        self.buffer_order = {}
        self.buffer_index = 1
        self.buffer_labels = self.buffer_ax.get_xticks().tolist()
        plt.grid()
        self.buffer_figure.canvas.draw()

    def update_buffer_round(self, number_of_round):
        self.buffer_figure.suptitle("Buffer Status " + number_of_round, size=16)

    def update_buffer(self, node, senders_shot):
        if self.buffer_order.get(node) is None:
            self.buffer_order[node] = self.buffer_index
            self.buffer_labels[self.buffer_index] = node
            self.buffer_ax.set_xticklabels(self.buffer_labels)
            self.buffer_ax.get_xticklabels()[self.buffer_index].set_color(self.buffer_colors[(self.buffer_index - 1)])
            self.buffer_index += 1

        senders_list = senders_shot.split(":")
        buffer_out = [pos for pos, char in enumerate(senders_list) if char == ""]
        self.lineOUT.set_xdata([self.buffer_order[node]] * len(buffer_out))
        self.lineOUT.set_ydata(buffer_out)
        self.buffer_ax.draw_artist(self.lineOUT)

        buffer_in = [pos for pos, char in enumerate(senders_list) if char != ""]
        
        self.lineIN.set_xdata([self.buffer_order[node]] * len(buffer_in))
        
        for pos in buffer_in:
            sender_node = senders_list[pos]
            if sender_node != "S":
                if self.buffer_order.get(sender_node) is not None:
                    color_position = self.buffer_order[sender_node] - 1
                    self.lineIN.set_color(self.buffer_colors[color_position])
                else:
                    self.lineIN.set_color("#FFFFFF")
            else:
                self.lineIN.set_color("#000000")
            self.lineIN.set_ydata(pos)
            self.buffer_ax.draw_artist(self.lineIN)
        
        self.buffer_figure.canvas.blit(self.buffer_ax.bbox)

    def plot_clr(self):
        self.clrs_per_round = []
        self.clr_figure, self.clr_ax = plt.subplots()
        self.lineCLR, = self.clr_ax.plot([1, 2], [10, 10], color='#000000', label="CLR", marker='o', ls='None', markeredgecolor='#000000', animated=True)
        self.clr_figure.suptitle("Chunk Loss Ratio", size=16)
        plt.legend(loc=2, numpoints=1)
        plt.axis([0, self.number_of_rounds, 0, 1])
        self.clr_figure.canvas.draw()

    def update_clrs(self, peer, clr):
        if peer in self.Type and self.Type[peer] != "MP":
            self.clrs_per_round.append(clr)

    def update_clr_plot(self, n_round):
        if len(self.clrs_per_round) > 0:
            self.lineCLR.set_xdata(float(n_round))
            self.lineCLR.set_ydata(np.mean(self.clrs_per_round))
            self.clr_ax.draw_artist(self.lineCLR)
            self.clr_figure.canvas.blit(self.clr_ax.bbox)
            self.clrs_per_round = []

    def draw(self):
        drawing_log_file = open(self.drawing_log, "r")

        # Read configuration from the first line
        line = drawing_log_file.readline()
        m = line.strip().split(";", 6)
        if m[0] == "C":
            self.number_of_monitors = int(m[1])
            self.number_of_peers = int(m[2])
            self.number_of_malicious = int(m[3])
            self.number_of_rounds = int(m[4])
            self.set_of_rules = m[5]
        else:
            self.lg.info("Invalid format file {}".format(self.drawing_log))
            exit()

        plt.ion()

        self.draw_net()
        self.plot_team()
        self.draw_buffer()
        self.plot_clr()
        time.sleep(1)
        line = drawing_log_file.readline()
        while line != "Bye":
            m = line.strip().split(";", 4)
            if m[0]=="MAP":
                self.Type[m[1]] = m[2] 
            if m[0] == "O":
                if m[1] == "Node":
                    if m[2] == "IN":
                        self.update_net(m[3], None, "IN")
                    else:
                        self.update_net(m[3], None, "OUT")
                else:
                    if m[2] == "IN":
                        self.update_net(None, (m[3], m[4]), "IN")
                    else:
                        self.update_net(None, (m[3], m[4]), "OUT")

            if m[0] == "T":
                self.update_team(m[1], m[2], m[3])

            if m[0] == "B":
                self.update_buffer(m[1], m[2])

            if m[0] == "CLR":
                self.update_clrs(m[1], float(m[2]))

            if m[0] == "R":
                self.update_clr_plot(m[1])
                # self.update_buffer_round(m[1])

            line = drawing_log_file.readline()

            # plt.ioff()
            # plt.show()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # lg.critical('Critical messages enabled.')
    # lg.error('Error messages enabled.')
    # lg.warning('Warning message enabled.')
    # lg.info('Informative message enabled.')
    # lg.debug('Low-level debug message enabled.')

    fire.Fire(Play)

    logging.shutdown()
