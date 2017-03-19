import pyqtgraph as pg
import numpy as np
import time

buffers={}

win = pg.GraphicsWindow()
p = win.addPlot()
p.setXRange(0,3)
p.setYRange(0,1024)
line1 = p.plot([1], [1], pen = 'r', symbol='o', clear=False)
line2 = p.plot([2], [1], pen = 'y', symbol='o', clear=False)

v=[]

for i in range(1024):
    v.append(i)
    #p.plot([1], [i], pen = 'r', symbol='o')
    #p.plot([2], [i], pen = 'y', symbol='o')
    line1.setData([1],[v[-1]])
    line2.setData([2],[v[-1]])
    pg.QtGui.QApplication.processEvents()
    #time.sleep(0.1)

