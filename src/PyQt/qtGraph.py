#!/usr/bin/env python3
import time

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui


class Graph(pg.GraphItem):
    defaultColor = (119, 136, 153, 255)

    def __init__(self):
        self.textItems = []
        pg.GraphItem.__init__(self)
        self.pos = []
        self.edges = [[0, 0]]    # edges should have atleast one edge else it will throw error
        self.texts = []
        self.V = 0
        self.lineColor = []
        self.nodeColors = []

    # Clear previous data and set new data, it is overrided to update nodes labels
    def setData(self, **kwds):
        self.text = kwds.pop('text', [])
        self.data = kwds
        if 'pos' in self.data:
            npts = self.data['pos'].shape[0]
            self.data['data'] = np.empty(npts, dtype=[('index', int)])
            self.data['data']['index'] = np.arange(npts)
        self.setTexts(self.text)
        self.updateGraph()

    def setTexts(self, text):
        for i in self.textItems:
            i.scene().removeItem(i)
        self.textItems = []
        for t in text:
            item = pg.TextItem(t)
            self.textItems.append(item)
            item.setParentItem(self)

    def updateGraph(self):
        pg.GraphItem.setData(self, **self.data)
        for i, item in enumerate(self.textItems):
            item.setPos(*self.data['pos'][i])

    def rescale_layout(self, pos, scale=1):
        # rescale to (-scale,scale) in all axes

        # shift origin to (0,0)
        lim = 0  # max coordinate for all axes
        for i in range(pos.shape[1]):
            pos[:, i] -= pos[:, i].mean()
            lim = max(pos[:, i].max(), lim)
        # rescale to (-scale,scale) in all directions, preserves aspect
        for i in range(pos.shape[1]):
            pos[:, i] *= scale/lim
        return pos

    # following algorithm is taken from networkx with some modification in it
        # this method would give positions to n nodes, so as to improve nodes visualisation
    def getNodePosn(self, n):
        if n == 1:
            return [[0, 0]]
        theta = np.linspace(0, 1, n + 1)[:-1] * 2 * np.pi   # Some trigonometic operations
        theta = theta.astype(np.float32)
        pos = np.column_stack([np.cos(theta), np.sin(theta)])
        pos = self.rescale_layout(pos, scale=1)+(0, 0)
        return pos

    def add_node(self, name, color=defaultColor):
        if name not in self.texts:
            self.pos = self.getNodePosn(self.V+1)   # Get position for V+1 nodes
            self.texts.append(name)
            self.nodeColors.append(color)
            self.setData(pos=np.array(self.pos, dtype=float),
                         adj=np.array(self.edges, dtype=int), size=0.1, pxMode=False, text=np.array(self.texts),
                         symbolBrush=np.array(self.nodeColors,
                                              dtype=[('red', np.ubyte),
                                                     ('green', np.ubyte), ('blue', np.ubyte), ('alpha', np.ubyte)]))
            self.updateGraph()
            self.V += 1
            # print("{} added ".format(name))

    def remove_node(self, name):
        if name not in self.texts:
            print("Such node not exist")
            return
        n = self.texts.index(name)
        self.edges = [[0, 0]] + [edge for edge in self.edges[1:] if edge[0] != n and edge[1] != n]
        for edge in self.edges:
            if edge[0] > n:
                edge[0] -= 1
            if edge[1] > n:
                edge[1] -= 1
        del self.nodeColors[n]
        del self.texts[n]
        self.V -= 1
        if self.V > 0:
            self.pos = self.getNodePosn(self.V)   # Get position for V-1 nodes
            self.setData(pos=np.array(self.pos, dtype=float),
                         adj=np.array(self.edges, dtype=int), size=0.1, pxMode=False, text=self.texts,
                         symbolBrush=np.array(self.nodeColors,
                                              dtype=[('red', np.ubyte), ('green', np.ubyte),
                                                     ('blue', np.ubyte), ('alpha', np.ubyte)]))
            print("{} removed ".format(name))

    def add_edge(self, edge):
        u = edge[0]
        v = edge[1]
        try:
            i = self.texts.index(u)
        except ValueError:
            self.add_node(u)
            i = self.texts.index(u)

        try:
            j = self.texts.index(v)
        except ValueError:
            self.add_node(u)
            j = self.texts.index(v)

        self._add_edge([i, j])
        # print("{} added".format(edge))

    def remove_edge(self, edge):
        u = edge[0]
        v = edge[1]
        try:
            i = self.texts.index(u)
            j = self.texts.index(v)
            self._remove_edge([i, j])
        except ValueError:
            print("No such edge exist")

        # print("{} removed".format(edge))

    def _add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)
            self.setData(pos=np.array(self.pos, dtype=float),
                         adj=np.array(self.edges, dtype=int), size=0.1, pxMode=False,
                         text=np.array(self.texts),
                         symbolBrush=np.array(self.nodeColors,
                                              dtype=[('red', np.ubyte), ('green', np.ubyte),
                                                     ('blue', np.ubyte), ('alpha', np.ubyte)]))

    def _remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
            self.setData(pos=np.array(self.pos, dtype=float),
                         adj=np.array(self.edges, dtype=int), size=0.1, pxMode=False,
                         text=np.array(self.texts),
                         symbolBrush=np.array(self.nodeColors,
                                              dtype=[('red', np.ubyte), ('green', np.ubyte),
                                                     ('blue', np.ubyte), ('alpha', np.ubyte)]))
            self.updateGraph()
        else:
            print("No such edge exist")


# For testing
if __name__ == '__main__':
    import sys
    import time
    # Enable antialiasing for prettier plots
    app = QtGui.QApplication([])

    pg.setConfigOptions(antialias=True)

    w = pg.GraphicsWindow()  # Create a window
    w.setWindowTitle('pyqtgraph example: CustomGraphItem')
    w.resize(800, 600)
    v = w.addViewBox()  # add a viewBox to window
    v.setAspectLocked()  # To lock aspect ratio

    g = Graph()  # Create a graph instance
    v.addItem(g)    # Add that instance into viewbox

    g.add_node('N0', (169, 188, 245, 255))  # That would a add a node
    g.add_node('N1')
    g.add_node('N2')
    g.add_node('N3')
    g.add_node('N4')

    add_edges = [['N0', 'N1'], ['N1', 'N2'], ['N0', 'N2'], ['N3', 'N4'], ['N1', 'N4']]

    for edge in add_edges:
        g.add_edge(edge)    # That would create an edge b/w u and v if edge=[u,v]
        app.processEvents()
        time.sleep(1)

    app.processEvents()
    remove_edges = [['N0', 'N1'], ['N1', 'N2'], ['N0', 'N2'], ['N3', 'N4'], ['N1', 'N4']]

    remove_node = ['N2', 'N1', 'N0', 'N3']
    for node in remove_node:
        g.remove_node(node)
        app.processEvents()
        time.sleep(1)

    app.processEvents()
    time.sleep(2)

    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    # QtGui.QApplication.instance().exec_()
