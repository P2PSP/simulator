#!/usr/bin/env python3
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
# pg.setConfigOptions(useOpenGL=True)
app = pg.mkQApp()   # A QtApp must be created before anyting else
from pyqtgraph import mkBrush,mkPen,mkColor
from qtGraph import Graph
import numpy as np
import matplotlib.cm as cm
pg.setConfigOption('background', 'w') #to change background to white
import time
import fire
import logging
import random
class Play():
    
    def __init__(self, drawing_log):
        self.drawing_log = drawing_log
        self.Type = {}
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.lg = logging.getLogger(__name__)
        self.lg.setLevel(logging.INFO)

    def get_team_size(self, n):
        return 2 ** (n - 1).bit_length()
        
    def get_buffer_size(self):
        team_size = self.get_team_size((self.number_of_monitors + self.number_of_peers + self.number_of_malicious) * 8)
        if (team_size < 32):
            return 32
        else:
            return team_size 
    
    def draw_net(self):
        pg.setConfigOptions(antialias=True)
        self.w = pg.GraphicsWindow()    # Create new window like matplotlib pyplot
        self.w.resize(800,600)
        self.w.setWindowTitle('Overlay Network of the Team')
        self.v = self.w.addViewBox()    #Add ViewBox that would contain all the graphics i.e graph structure
        self.v.setAspectLocked()
        self.G = Graph()        #Child class of pg.GraphItem that would contain all the nodes and edges
        self.v.addItem(self.G)  
        self.color_map = {'peer': (169,188,245,255), 'monitor': (169,245,208,255), 'malicious': (247,129,129,255)}

    def update_net(self, node, edge, direction):
        # self.lg.info("Update net", node, edge, direction)
        if node:
            if node in self.Type and self.Type[node] == "MP":
                if direction == "IN":
                    self.G.add_node(node,self.color_map['malicious'])
                else:
                    self.lg.info("simulator: {} removed from graph (MP)".format(node))
                    self.G.remove_node(node)
            elif node in self.Type and self.Type[node] == "M":
                if direction == "IN":
                    self.G.add_node(node,self.color_map['monitor'])
                else:
                    self.G.remove_node(node)
            else:
                if direction == "IN":
                    self.G.add_node(node,self.color_map['peer'])
                else:
                    self.G.remove_node(node)
        else:
            if direction == "IN":
                self.G.add_edge(edge)
            else:
                self.G.add_edge(edge)

    def plot_team(self):
        # these would contain list of x coordinates
        self.Monitors_rounds = []
        self.WIPs_rounds = []
        self.MPs_rounds = []
        # these would contain list of yc coordinates
        self.Monitors_qty = []
        self.WIPs_qty= []
        self.MPs_qty = []
        self.win = pg.GraphicsLayoutWidget()
        self.win.setWindowTitle("Number of Peers in the Team")
        self.win.resize(800,600)

        # Enable antialiasing for prettier plots
        # pg.setConfigOptions(antialias=True)
        self.p3 = self.win.addPlot()    # Adding plot to window like matplotlib subplot method
        self.p3.addLegend()
        # Create separate plots to handle regular,monitor and malicious peer it is much like matplotlib plot method
        self.lineWIPs = self.p3.plot(pen=(None), symbolBrush=(0,0,255), symbolPen='b',name='#WIP')  
        self.lineMonitors = self.p3.plot(pen=(None), symbolBrush=(0,255,0), symbolPen='g',name='#Monitors Peers')
        self.lineMPs = self.p3.plot( pen=(None), symbolBrush=(255,0,0), symbolPen='r',name='Malicious Peers')
        
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        self.p3.setRange(xRange=[0,self.number_of_rounds],yRange=[0,total_peers])
        self.win.show()


    def update_team(self, node, quantity, n_round):
        if node == "M":
            self.Monitors_rounds.append(float(n_round))
            self.Monitors_qty.append(float(quantity))
            self.lineMonitors.setData(self.Monitors_rounds,self.Monitors_qty) # Clear the previous data and set new data to plot
        elif node == "P":
            self.WIPs_rounds.append(float(n_round))
            self.WIPs_qty.append(float(quantity))
            self.lineWIPs.setData(self.WIPs_rounds,self.WIPs_qty)
        else:
            self.MPs_rounds.append(float(n_round))
            self.MPs_qty.append(float(quantity))
            self.lineMPs.setData(self.MPs_rounds,self.MPs_qty)

    def draw_buffer(self):
        self.buff_win = pg.GraphicsLayoutWidget()
        self.buff_win.setWindowTitle('Buffer Status')
        self.buff_win.resize(800,700)

        self.total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        self.p4 = self.buff_win.addPlot()
        self.p4.showGrid(x=True,y=True,alpha=100)   # To show grid lines across x axis and y axis
        leftaxis = self.p4.getAxis('left') # get left axis i.e y axis 
        leftaxis.setTickSpacing(5,1)    # to set ticks at a interval of 5 and grid lines at 1 space
        
        # Get different colors using matplotlib library
        if self.total_peers <8:
            colors = cm.Set2(np.linspace(0, 1, 8))
        elif self.total_peers <12:
            colors = cm.Set3(np.linspace(0,1,12))
        else:
            colors = cm.rainbow(np.linspace(0,1,self.total_peers+1))
        self.QColors = [pg.hsvColor(color[0],color[1],color[2],color[3]) for color in colors]   # Create QtColors, each color would represent a peer

        self.Data = []  # To represent buffer out  i.e outgoing data from buffer
        self.OutData = []   # To represent buffer in i.e incoming data in buffer

        # a single line would reperesent a single color or peer, hence we would not need to pass a list of brushes
        self.lineIN = [None]*self.total_peers  
        for ix in range(self.total_peers):
            self.lineIN[ix] = self.p4.plot(pen=(None),symbolBrush=self.QColors[ix],name='IN',symbol='o',clear=False)
            self.Data.append(set())
            self.OutData.append(set())

        # similiarly one line per peer to represent outgoinf data from buffer
        self.lineOUT = self.p4.plot(pen=(None),symbolBrush=mkColor('#CCCCCC'),name='OUT',symbol='o',clear=False)
        self.p4.setRange(xRange=[0,self.total_peers],yRange=[0,self.get_buffer_size()])
        self.buff_win.show()    # To actually show create window

        self.buffer_order = {}
        self.buffer_index = 0
        self.buffer_labels = []
        self.lastUpdate = pg.ptime.time()
        self.avgFps = 0.0

    def update_buffer_round(self, number_of_round):
        self.buff_win.setWindowTitle("Buffer Status " + number_of_round)

    def update_buffer(self, node, senders_shot):
        
        if self.buffer_order.get(node) is None:
            self.buffer_order[node] = self.buffer_index
            self.buffer_labels.append(node)
            text = pg.TextItem()
            text.setText("P"+str(self.buffer_index))
            text.setColor(self.QColors[self.buffer_index])
            text.setFont(QtGui.QFont("arial", 16))
            text.setPos(self.buffer_index, 1)
            self.p4.addItem(text)   # Add label for newly added peer
            self.buffer_index += 1

        senders_list = senders_shot.split(":")
        buffer_order_node = self.buffer_order[node]
        self.OutData[buffer_order_node].clear()

        for pos,sender in enumerate(senders_list):
            self.clear_all((buffer_order_node,pos)) # Clear previous color point, to avoid overapping 
            if sender!="":
                ix = self.buffer_order[sender]
                self.Data[ix].add((buffer_order_node,pos))
            else:
                self.OutData[buffer_order_node].add((buffer_order_node,pos))

        ######
        xIn = []
        yIn = []
        for i in range(self.total_peers):
            tempData  = list(self.Data[i])
            xIn.append([])
            yIn.append([])
            for pt in tempData:
                xIn[i].append(pt[0])
                yIn[i].append(pt[1])

        xOut = []
        yOut = []
        for i in range(self.total_peers):
            tempData = list(self.OutData[i])
            for pt in tempData:
                xOut.append(pt[0])
                yOut.append(pt[1])
        ######

        self.lineOUT.setData(x=xOut,y=yOut)
        for ix in range(self.total_peers):
            self.lineIN[ix].setData(x=xIn[ix],y=yIn[ix])

    def clear_all(self,pt):
        for ix in range(self.total_peers):
            if pt in self.Data[ix]:
                self.Data[ix].remove(pt)

    def plot_clr(self):
        self.clrs_per_round = []
        self.clr_win = pg.GraphicsLayoutWidget()
        self.clr_win.setWindowTitle('Chunk Loss Ratio')
        self.clr_win.resize(800,700)
        self.clr_figure = self.clr_win.addPlot()
        self.clr_figure.addLegend()
        self.lineCLR = self.clr_figure.plot( pen=(None),symbolBrush=mkColor('#000000'), name="CLR", symbol='o', clear=True)
        self.clr_figure.setRange(xRange=[0,self.number_of_rounds],yRange=[0,1])
        self.clrData = [[],[]]  # 2D list to store both the x and y coordinates
        self.clr_win.show()

    def update_clrs(self, peer, clr):
        if peer in self.Type and self.Type[peer] != "MP":
            self.clrs_per_round.append(clr)

    def update_clr_plot(self, n_round):
        if len(self.clrs_per_round) > 0:
            self.clrData[0].append(n_round)
            self.clrData[1].append(np.mean(self.clrs_per_round))
            self.lineCLR.setData(x=self.clrData[0],y=self.clrData[1])
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

        self.draw_net()
        self.plot_team()
        self.draw_buffer()
        self.plot_clr()
        time.sleep(1)
        line = drawing_log_file.readline()
        while line != "Bye":
            m = line.strip().split(";", 4)
            if m[0] == "MAP":
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
                self.update_clr_plot(int(m[1]))

            if m[0] !="B":      # if skip over intermediate buffer states, then plotting speed would increase by 2X
                app.processEvents()       # This would process all the Qt operations done so far
            line = drawing_log_file.readline()


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    fire.Fire(Play)

    logging.shutdown()

