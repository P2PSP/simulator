import matplotlib.pyplot as plt

plt.ion()
buffers = {}

fig, ax = plt.subplots()
lines = []
# for i in range(6):
#    line, = ax.plot([i], 0, color = '#A9F5D0', marker='o', animated=True)
#    lines.append(line)

line, = ax.plot([1, 2, 3, 4, 5, 6], [1] * 6, color='#A9F5D0', ls='None', marker='o', markeredgecolor='#A9F5D0',
                animated=True)

plt.suptitle("Buffer Status", size=16)
plt.axis([0, 6, 0, 1024])
fig.canvas.draw()
v = []

# bk = fig.canvas.copy_from_bbox(ax.bbox)
for i in range(1024):
    v.append(i)
    # for j in range(6):
    # fig.canvas.restore_region(bk)
    # lines[j].set_xdata(j+1)
    # lines[j].set_ydata(v[-1])
    # ax.draw_artist(lines[j])
    line.set_ydata(i * 6)
    ax.draw_artist(line)
    fig.canvas.blit(ax.bbox)
    # bk = fig.canvas.copy_from_bbox(ax.bbox)

    # fig.canvas.get_tk_widget().update()
    # fig.canvas.flush_events()
    # plt.pause(0.001)
    # fig.canvas.get_tk_widget().update()

plt.ioff()
plt.show()
