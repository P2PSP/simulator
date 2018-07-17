import matplotlib.pyplot as plt

plt.ion()
buffers = {}

fig = plt.figure()
plt.suptitle("Buffer Status", size=16)
plt.axis([0, 6, 0, 1024])
v = []
for i in range(1024):
    v.append(i)
    plt.plot([1], i, color='#A9F5D0', marker='o')
    plt.plot([2], i, color='#CCCCCC', marker='o')
    fig.canvas.draw()

plt.ioff()
plt.show()
