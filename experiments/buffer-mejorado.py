import matplotlib.pyplot as plt

plt.ion()
buffers={}

fig, ax = plt.subplots()
line1, = ax.plot([1], 0, color = '#A9F5D0', marker='o', animated=True)
line2, = ax.plot([2], 0, color = '#CCCCCC', marker='o', animated=True)
plt.suptitle("Buffer Status", size=16)
plt.axis([0, 6, 0, 1024])
fig.canvas.draw()
v = []

bk = fig.canvas.copy_from_bbox(ax.bbox)
for i in range(1024):
    v.append(i)
    fig.canvas.restore_region(bk)
    line1.set_xdata([1]*len(v))
    line1.set_ydata([v])
    ax.draw_artist(line1)

    line2.set_xdata([2]*len(v))
    line2.set_ydata([v])
    ax.draw_artist(line2)
    
    fig.canvas.blit(ax.bbox)
    #fig.canvas.get_tk_widget().update()
    #fig.canvas.flush_events()
    #plt.pause(0.001)
    #fig.canvas.get_tk_widget().update()
    
plt.ioff()
plt.show()
