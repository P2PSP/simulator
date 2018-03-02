import threading
import time
import random
import queue
import datetime

queue_length = 10
q = queue.Queue(queue_length)


class send(threading.Thread):
    def __init__(self, item, delay=10):
        super(send, self).__init__()
        self.delay = delay
        self.item = item

    def run(self):
        print(datetime.datetime.now().time(), "Sending", self.item)
        time.sleep(self.delay)
        q.put(self.item)
        print(datetime.datetime.now().time(), "Sent", self.item)


class Producer(threading.Thread):
    def __init__(self, iters=10):
        super(Producer, self).__init__()
        self.iters = iters

    def run(self):
        i = 0
        while i < self.iters:
            if not q.full():
                item = random.randint(1, 10)
                # send(item,item/100.0).start()
                send(item, 10).start()
                # send(item,0).start()
                # q.put(item)
                print('Produced {} (queue length = {})'.format(item, q.qsize()))
                i += 1
                time.sleep(random.random())
        return


class Consumer(threading.Thread):
    def __init__(self, iters=10):
        super(Consumer, self).__init__()
        self.iters = iters

    def run(self):
        i = 0
        while i < self.iters:
            if not q.empty():
                item = q.get()
                print('Consumed {} (queue length = {})'.format(item, q.qsize()))
                i += 1
                time.sleep(random.random())
        return


Producer().start()
Consumer().start()
