from core.encoder import encoder
from core.splitter_dbs import Splitter_DBS
from core.splitter_strpeds import Splitter_STRPEDS
from core.splitter_sss import Splitter_SSS
from core.peer_dbs import Peer_DBS
from core.peer_strpeds import Peer_STRPEDS
from core.peer_sss import Peer_SSS
from core.peer_malicious import Peer_Malicious
from core.peer_malicious_sss import Peer_Malicious_SSS
from core.monitor_dbs import Monitor_DBS
from core.monitor_strpeds import Monitor_STRPEDS
from core.monitor_sss import Monitor_SSS
from core.common import Common
from core.simulator_stuff import Simulator_stuff as sim
#from core.simulator_stuff import lg
from multiprocessing import Process, Queue, Manager
from glob import glob
import time
import fire
if __debug__:
    import networkx as nx
    #import matplotlib.pyplot as plt
    #import matplotlib.cm as cm
import numpy as np
import platform
import os
import logging

#import logging as lg

class Simulator():

    P_IN = 0.4
    P_MoP = 0.2
    P_WIP = 0.6
    P_MP = 0.2

    def __init__(self, drawing_log, set_of_rules=None, number_of_monitors=0, number_of_peers=0, number_of_rounds=0, number_of_malicious=0, gui=False):

        self.lg = logging.getLogger(__name__)
        #self.lg = logging.getLogger(__name__)
        #handler = logging.StreamHandler()
        #formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        #formatter = logging.Formatter(fmt='peer_dbs.py - %(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',datefmt='%H:%M:%S')
        #handler.setFormatter(formatter)
        #self.lg.addHandler(handler)
        self.lg.setLevel(logging.ERROR)
        self.lg.critical('Critical messages enabled.')
        self.lg.error('Error messages enabled.')
        self.lg.warning('Warning message enabled.')
        self.lg.info('Informative message enabled.')
        self.lg.debug('Low-level debug message enabled.')

        
        self.set_of_rules = set_of_rules
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors
        self.drawing_log = drawing_log
        self.number_of_rounds = number_of_rounds
        self.number_of_malicious = number_of_malicious
        self.current_round = 0
        self.gui = gui
        self.processes = {}

    def get_team_size(self, n):
        return 2**(n-1).bit_length()

    def get_buffer_size(self):
        #return self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        team_size = self.get_team_size((self.number_of_monitors + self.number_of_peers + self.number_of_malicious)*8)
        if (team_size < 32):
            return 32
        else:
            return team_size

    def run_a_splitter(self):
        Common.BUFFER_SIZE = self.get_buffer_size()
        if self.set_of_rules == "dbs":
            splitter = Splitter_DBS()
        elif self.set_of_rules == "cis":
            splitter = Splitter_STRPEDS()
        elif self.set_of_rules == "cis-sss":
            splitter = Splitter_SSS()

        #splitter.start()
        splitter.run()
        #while splitter.alive:
        #    time.sleep(1)

    def run_a_peer(self, splitter_id, type, id, first_monitor=False):
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        chunks_before_leave = np.random.weibull(2) * (total_peers*(self.number_of_rounds-self.current_round))
        if type == "monitor":
            if first_monitor is True:
                chunks_before_leave = 99999999
            if self.set_of_rules == "dbs":
                peer = Monitor_DBS(id)
            elif self.set_of_rules == "cis":
                self.lg.info("simulator: Monitors are TPs in CIS")
                peer = Monitor_STRPEDS(id)
            elif self.set_of_rules == "cis-sss":
                self.lg.info("simulator: Monitors are TPs in CIS")
                peer = Monitor_SSS(id)
        elif type == "malicious":
            if self.set_of_rules == "cis":
                peer = Peer_Malicious(id)
            elif self.set_of_rules == "cis-sss":
                peer = Peer_Malicious_SSS(id)
            else:
                self.lg.info("simulator: Malicious peers are only compatible with CIS")
        else:
            if self.set_of_rules == "dbs":
                peer = Peer_DBS(id)
            elif self.set_of_rules == "cis":
                peer = Peer_STRPEDS(id)
            elif self.set_of_rules == "cis-sss":
                peer = Peer_SSS(id)
        self.lg.info("simulator: {}: alive till consuming {} chunks".format(id, chunks_before_leave))

        peer.chunks_before_leave = chunks_before_leave
        peer.set_splitter(splitter_id)
        peer.connect_to_the_splitter()
        peer.receive_buffer_size()
        peer.receive_the_number_of_peers()
        peer.listen_to_the_team()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        #peer.buffer_data()
        #peer.start()
        peer.run()

        '''
        while not peer.ready_to_leave_the_team:
            if type != "malicious" and peer.number_of_chunks_consumed >= chunks_before_leave and peer.player_alive:
                self.lg.info("simulator:", id, "reached the number of chunks consumed before leave", peer.number_of_chunks_consumed)
                peer.player_alive = False
            time.sleep(1)
        '''
        self.lg.info("simulator: {}: left the team".format(id))

    def store(self):
        drawing_log_file = open(self.drawing_log, "w", 1)

        # Configuration in the first line
        m = ["C", self.number_of_monitors, self.number_of_peers, self.number_of_malicious, self.number_of_rounds, self.set_of_rules]
        drawing_log_file.write(";".join(map(str, m))+'\n')

        queue = sim.FEEDBACK["DRAW"]
        m = queue.get()

        while m[0] != "Bye":
            #drawing_log_file.write(";".join(map(str, m))+'\n')
            # Sometimes the queue doesn't receive Bye message.
            #try:
            m = queue.get()
            if len(m)==4:
                aux = str(m[0])+";"+str(m[1])+";"+encoder(str(m[2]))+";"+str(m[3])
                drawing_log_file.write(aux+"\n")
            #except:
            #    break

        drawing_log_file.write("Bye")
        self.lg.info("CLOSING STORE")
        drawing_log_file.close()

    def run(self):
        self.lg.info("simulator: platform.system() = {}".format(platform.system()))
        # if __debug__:
        #     if platform.system() == 'Linux':
        #         plt.switch_backend("TkAgg")
        #     elif platform.system() == 'Darwin':
        #         plt.switch_backend("macosx")
        #         plt.style.use("seaborn-white")

        # Removing temporal socket files
        for pattern in ['*_udp', '*_tcp']:
            for tmp_file in glob(pattern):
                os.remove(tmp_file)
        
        # Listen to the team for drawing
        sim.FEEDBACK["DRAW"] = Queue()
        Process(target=self.store).start()

        if __debug__:
            if self.gui is True:
                Process(target=self.draw).start()

        # Listen to the team for simulation life
        sim.FEEDBACK["STATUS"] = Queue()

        # create shared list for CIS set of rules (only when cis is choosen?)
        manager = Manager()
        sim.SHARED_LIST["malicious"] = manager.list()
        sim.SHARED_LIST["regular"] = manager.list()
        sim.SHARED_LIST["attacked"] = manager.list()

        # Automatic bitrate control only for CIS-SSS
        sim.RECV_LIST = manager.dict()
        #sim.LOCK = Semaphore()

        # run splitter
        p = Process(target=self.run_a_splitter)
        p.start()
        self.processes["S"] = p.pid
        self.attended_monitors = 0
        self.attended_peers = 0
        self.attended_mps = 0

        # run a monitor
        p = Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+0), True])
        p.start()
        self.processes["M"+str(self.attended_monitors+1)] = p.pid
        self.attended_monitors += 1

        queue = sim.FEEDBACK["STATUS"]
        m = queue.get()
        while m[0] != "Bye" and self.current_round < self.number_of_rounds:
            if (m[0] == "R"):
                self.current_round = m[1]
                r = np.random.uniform(0, 1)
                if r <= Simulator.P_IN:
                    self.addPeer()
            m = queue.get()

        sim.FEEDBACK["DRAW"].put(("Bye", "Bye"))
        sim.FEEDBACK["STATUS"].put(("Bye", "Bye"))
        for name, pid in self.processes.items():
            self.lg.info("Killing {}, ...".format(name))
            os.system("kill -9 "+str(pid))
            self.lg.info("{} killed".format(name))
            
        if self.set_of_rules == "cis" or self.set_of_rules == "cis-sss":
            self.lg.info("List of Malicious")
            self.lg.info(sim.SHARED_LIST["malicious"])
            self.lg.info("List of Regular detected")
            self.lg.info(sim.SHARED_LIST["regular"])
            self.lg.info("List of peer Attacked")
            self.lg.info(sim.SHARED_LIST["attacked"])
            
    def addPeer(self):
        probabilities = [Simulator.P_MoP, Simulator.P_WIP, Simulator.P_MP]
        option = np.where(np.random.multinomial(1, probabilities))[0][0]
        if option == 0:
            if self.attended_monitors < self.number_of_monitors:
                p = Process(target=self.run_a_peer, args=["S", "monitor", "M"+str(self.attended_monitors+0)])
                p.start()
                self.processes["M"+str(self.attended_monitors+1)] = p.pid
                self.attended_monitors += 1
        elif option == 1:
            if self.attended_peers < self.number_of_peers:
                p = Process(target=self.run_a_peer, args=["S", "peer", "P"+str(self.attended_peers+1)])
                p.start()
                self.processes["P"+str(self.attended_peers+1)] = p.pid
                self.attended_peers += 1
        elif option == 2:
            if self.attended_mps < self.number_of_malicious:
                p = Process(target=self.run_a_peer, args=["S", "malicious", "MP"+str(self.attended_mps+1)])
                p.start()
                self.processes["MP"+str(self.attended_mps+1)] = p.pid
                self.attended_mps += 1

if __name__ == "__main__":
    
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #lg.critical('Critical messages enabled.')
    #lg.error('Error messages enabled.')
    #lg.warning('Warning message enabled.')
    #lg.info('Informative message enabled.')
    #lg.debug('Low-level debug message enabled.')

    fire.Fire(Simulator)

    logging.shutdown()
