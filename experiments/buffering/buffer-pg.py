import pyqtgraph as pg
import numpy as np
import time

buffers = {}

win = pg.GraphicsWindow()
p = win.addPlot()
p.setXRange(0, 10)
p.setYRange(0, 1024)
line = p.plot([1, 2], [1] * 2, pen='r', symbol='o')

a = []
b = []

v = [1] * 1024
w = []
for i in range(1024):
    v[i] = i
    a.append(1)
    b.append(2)
    # p.plot([1], [i], pen = 'r', symbol='o')
    # p.plot([2], [i], pen = 'r', symbol='o')
    # p.plot(a[-156:]+b[-156:], v[-156:]*2, pen = 'y', symbol='o', clear=True)
    line.setData([1, 2], [v[i]] * 2)
    # p.plot([j+1], [v[-1]], pen = 'r', symbol='o', clear=True)
    pg.QtGui.QApplication.processEvents()
    # time.sleep(0.1)
