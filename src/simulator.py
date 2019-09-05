#!/home/vruiz/.pyenv/shims/python -i

import logging
import os
import platform
import time
from glob import glob
# from core.simulator_stuff import lg
from multiprocessing import Manager, Process, Queue

import fire
# import networkx as nx
# import matplotlib.pyplot as plt
# import matplotlib.cm as cm
import numpy as np

from core.common import Common
#from core.monitor_dbs_latency import Monitor_DBS_latency as Monitor_DBS
from core.monitor_dbs import Monitor_DBS
from core.monitor_dbs_simulator import Monitor_DBS_simulator
from core.monitor_ims import Monitor_IMS
from core.monitor_ims_simulator import Monitor_IMS_simulator
from core.monitor_sss import Monitor_SSS
from core.monitor_strpeds import Monitor_STRPEDS
#from core.peer_dbs_latency import Peer_DBS_latency as Peer_DBS
from core.peer_dbs import Peer_DBS
from core.peer_dbs_simulator import Peer_DBS_simulator
from core.peer_ims import Peer_IMS
from core.peer_ims_simulator import Peer_IMS_simulator
from core.peer_malicious import Peer_Malicious
from core.peer_malicious_sss import Peer_Malicious_SSS
from core.peer_sss import Peer_SSS
from core.peer_strpeds import Peer_STRPEDS
from core.simulator_stuff import Simulator_stuff as sim
#from core.splitter_dbs_latency import Splitter_DBS_latency as Splitter_DBS
from core.splitter_dbs import Splitter_DBS
from core.splitter_dbs_simulator import Splitter_DBS_simulator
from core.splitter_sss import Splitter_SSS
from core.splitter_strpeds import Splitter_STRPEDS
import sys

# import logging as lg


class Simulator():
    P_IN = 1.0  # 0.4
    P_MoP = 0.0  # 0.2
    P_WIP = 1.0  # 0.6
    P_MP = 0.0  # 0.2

    def __init__(self, drawing_log="/tmp/drawing_log.txt",
                 set_of_rules="DBS",
                 number_of_monitors=1,
                 number_of_peers=9,
                 number_of_rounds=100,
                 number_of_malicious=0,
                 buffer_size=32,
                 chunk_cadence=0.01,
                 link_failure_prob=0.0,
                 max_degree=5,
                 loglevel=logging.ERROR,
                 gui=False):

        #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        #self.lg = ColorLog(logging.getLogger(__name__))
        self.lg = logging.getLogger(__name__)
        self.loglevel = loglevel
        self.lg.setLevel(loglevel)
        # self.lg.critical('Critical messages enabled.')
        # self.lg.error('Error messages enabled.')
        # self.lg.warning('Warning message enabled.')
        # self.lg.info('Informative message enabled.')
        # self.lg.debug('Low-level debug message enabled.')

        self.set_of_rules = set_of_rules
        self.number_of_peers = int(number_of_peers)
        self.number_of_monitors = int(number_of_monitors)
        self.drawing_log = drawing_log
        self.number_of_rounds = int(number_of_rounds)
        self.number_of_malicious = number_of_malicious
        self.buffer_size = int(buffer_size)
#        self.chunk_cadence = float(chunk_cadence)
#        self.link_failure_prob = link_failure_prob
#        self.optimization_horizon = int(optimization_horizon)
#        self.max_chunk_loss_at_peers = int(max_chunk_loss_at_peers)
#        self.max_chunk_loss_at_splitter = int(max_chunk_loss_at_splitter)
        self.current_round = 0
        self.gui = gui
        self.processes = {}

        self.lg.info(f"set_of_rules=\"{self.set_of_rules}\"")
        sys.stderr.write(f"simulator: set_of_rules=\"{self.set_of_rules}\"\n")
        self.lg.info(f"number_of_peers={self.number_of_peers}")
        sys.stderr.write(f"simulator: number_of_peers={self.number_of_peers}\n")
        self.lg.info(f"number_of_monitors={self.number_of_monitors}")
        sys.stderr.write(f"simulator: number_of_monitors={self.number_of_monitors}\n")
        self.lg.info(f"number_of_rounds={self.number_of_rounds}")
        sys.stderr.write(f"simulator: number_of_rounds={self.number_of_rounds}\n")
        self.lg.info(f"number_of_malicious={self.number_of_malicious}")
        sys.stderr.write(f"simulator: number_of_malicious={self.number_of_malicious}\n")
        self.lg.info(f"buffer_size={self.buffer_size}")
        sys.stderr.write(f"simulator: buffer_size={self.buffer_size}\n")
#        self.lg.info(f"chunk_cadence={self.chunk_cadence}")
#        sys.stderr.write(f"simulator: chunk_cadence={self.chunk_cadence}\n")
#        self.lg.info(f"optimization_horizon={self.optimization_horizon}")
#        sys.stderr.write(f"simulator: optimization_horizon={self.optimization_horizon}\n")
#        self.lg.info(f"max_chunk_loss_at_peers={self.max_chunk_loss_at_peers}")
#        sys.stderr.write(f"simulator: max_chunk_loss_at_peers={self.max_chunk_loss_at_peers}\n")
#        self.lg.info(f"max_chunk_loss_at_splitter={self.max_chunk_loss_at_splitter}")
#        sys.stderr.write(f"simulator: max_chunk_loss_at_splitter={self.max_chunk_loss_at_splitter}\n")
        self.lg.info(f"loglevel={self.loglevel}")
        sys.stderr.write(f"simulator: loglevel={self.loglevel}\n")

    def compute_team_size(self, n):
        return 2 ** (n - 1).bit_length()

    def compute_buffer_size(self):
        # return self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        team_size = self.compute_team_size(
            (self.number_of_monitors + self.number_of_peers + self.number_of_malicious) * 8)
        if (team_size < 32):
            return 32
        else:
            return team_size

    def run_a_splitter(self, splitter_id):
        """ Start a splitter
        """
#        Common.CHUNK_CADENCE = self.chunk_cadence
        if self.buffer_size == 0:
            Common.BUFFER_SIZE = self.compute_buffer_size()
        else:
            Common.BUFFER_SIZE = self.buffer_size
        self.lg.debug("(definitive) buffer_size={}".format(Common.BUFFER_SIZE))
        if self.set_of_rules == "DBS" or self.set_of_rules == "IMS":
            Splitter_DBS.splitter_port = 0
            Splitter_DBS.max_chunk_loss = 8
            Splitter_DBS.number_of_monitors = 1
            Splitter_DBS.buffer_size = Common.BUFFER_SIZE
            splitter = Splitter_DBS_simulator("Splitter_DBS_simulator")
            self.lg.info("simulator: DBS/IMS splitter created")
        elif self.set_of_rules == "CIS":
            splitter = Splitter_STRPEDS()
            self.lg.info("simulator: CIS splitter created")
        elif self.set_of_rules == "CIS-SSS":
            splitter = Splitter_SSS()
            self.lg.info("simulator: CIS-SSS splitter created")

        # splitter.start()
        splitter.setup_peer_connection_socket()
        splitter.setup_team_socket()
        splitter_id['address'] = splitter.get_id()
        splitter.max_number_of_rounds = self.number_of_rounds
        splitter.run()
        # while splitter.current_round < self.number_of_rounds:
        #    self.lg.info("{}: splitter.current_round = {}".format(self.id, splitter.current_round))
        #    time.sleep(1)
        #splitter.alive = False
        # while splitter.alive:
        #    time.sleep(1)

    def run_a_peer(self, splitter_id, type, id, first_monitor=False):
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_malicious
        chunks_before_leave = np.random.weibull(2) * (total_peers * (self.number_of_rounds - self.current_round))
        self.lg.info("simulator: creating {}".format(type))
        if type == "monitor":
            if first_monitor is True:
                pass
                #chunks_before_leave = 99999999
            if self.set_of_rules == "DBS":
                peer = Monitor_DBS_simulator(id, "Monitor_DBS_simulator", self.loglevel)
                self.lg.info("simulator: DBS monitor created")
            elif self.set_of_rules == "IMS":
                peer = Monitor_IMS_simulator(id, "Monitor_IMS_simulator", self.loglevel)
                self.lg.info("simulator: IMS monitor created")
            elif self.set_of_rules == "CIS":
                peer = Monitor_STRPEDS(id)
                self.lg.info("simulator: STRPEDS monitor created")
            elif self.set_of_rules == "CIS-SSS":
                peer = Monitor_SSS(id)
                self.lg.info("simulator: SSS monitor created")
        elif type == "malicious":
            if self.set_of_rules == "CIS":
                peer = Peer_Malicious(id)
                self.lg.info("simulator: CIS malicious created")
            elif self.set_of_rules == "CIS-SSS":
                peer = Peer_Malicious_SSS(id)
                self.lg.info("simulator: CIS-SSS malicious created")
            else:
                self.lg.info("simulator: Malicious peers are only compatible with CIS")
        else:
            if self.set_of_rules == "DBS":
                peer = Peer_DBS_simulator(id, "Peer_DBS_simulator", self.loglevel)
                self.lg.info("simulator: DBS peer created")
            if self.set_of_rules == "IMS":
                peer = Peer_IMS_simulator(id, "Peer_IMS_simulator", self.loglevel)
                self.lg.info("simulator: IMS peer created")
            elif self.set_of_rules == "CIS":
                peer = Peer_STRPEDS(id)
                self.lg.info("simulator: CIS peer created")
            elif self.set_of_rules == "CIS-SSS":
                peer = Peer_SSS(id)
                self.lg.info("simulator: CIS-SSS peer created")
        self.lg.critical("simulator: {}: alive till consuming {} chunks".format(id, chunks_before_leave))

#        peer.link_failure_prob = self.link_failure_prob
#        peer.max_degree = self.max_degree
        peer.chunks_before_leave = chunks_before_leave
        peer.splitter = splitter_id
        peer.connect_to_the_splitter(peer_port=0)
        peer.receive_public_endpoint()
        peer.receive_buffer_size()
        peer.receive_the_number_of_peers()
        peer.listen_to_the_team()
        peer.receive_the_list_of_peers()
        #peer.send_ready_for_receiving_chunks()
        #peer.send_peer_type()   #Only for simulation purpose
        # peer.buffer_data()
        # peer.start()
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
        """Create a log file for drawing
        """
        drawing_log_file = open(self.drawing_log, "w", 1)

        # Configuration in the first line
        m = ["C", self.number_of_monitors, self.number_of_peers, self.number_of_malicious, self.number_of_rounds,
             self.set_of_rules]
        drawing_log_file.write(";".join(map(str, m)) + '\n')

        queue = sim.FEEDBACK["DRAW"]
        m = queue.get()

        while m[0] != "Bye":
            drawing_log_file.write(";".join(map(str, m))+'\n')
            # Sometimes the queue doesn't receive Bye message.
            # try:
            m = queue.get()
            # except:
            #    break

        drawing_log_file.write("Bye")
        self.lg.info("CLOSING STORE")
        drawing_log_file.close()

    def run(self):
        #import pdb; pdb.set_trace()
        self.lg.info("simulator: platform.system()={}".format(platform.system()))
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

        if self.gui is True:
            Process(target=self.draw).start()

        # Listen to the team for simulation life
        sim.FEEDBACK["STATUS"] = Queue()

        # Create shared list for CIS set of rules (only when cis is chosen?)
        manager = Manager()
        sim.SHARED_LIST["malicious"] = manager.list()
        sim.SHARED_LIST["regular"] = manager.list()
        sim.SHARED_LIST["attacked"] = manager.list()

        # Automatic bitrate control only for CIS-SSS
        sim.RECV_LIST = manager.dict()
        # sim.LOCK = Semaphore()

        # Share splitter (ip address,port) with peers
        self.splitter_id = manager.dict()

        # Run splitter
        p = Process(target=self.run_a_splitter,args=[self.splitter_id])
        p.start()
        self.processes["S"] = p.pid
        self.attended_monitors = 0
        self.attended_peers = 0
        self.attended_mps = 0

        time.sleep(1)
        # run a monitor
        p = Process(target=self.run_a_peer, args=[self.splitter_id['address'], "monitor", "M" + str(self.attended_monitors + 0), True])
        p.start()
        self.processes["M" + str(self.attended_monitors + 1)] = p.pid
        self.attended_monitors += 1

        queue = sim.FEEDBACK["STATUS"]
        m = queue.get()
        while m[0] != "Bye" and self.current_round < self.number_of_rounds:
            if m[0] == "R":
                self.current_round = m[1]
                r = np.random.uniform(0, 1)
                if (r <= Simulator.P_IN) and (self.current_round < self.number_of_rounds):
                    self.addPeer()
            m = queue.get()
            #import pdb; pdb.set_trace()
            #sys.stderr.write("round = {}/{}\n".format(self.current_round, self.number_of_rounds))
            #print("------------------> round = {}/{} <-----------------------".format(self.current_round, self.number_of_rounds))

        sim.FEEDBACK["DRAW"].put(("Bye", "Bye"))
        sim.FEEDBACK["STATUS"].put(("Bye", "Bye"))
        for name, pid in self.processes.items():
            self.lg.info("Killing {}, ...".format(name))
            os.system("kill -9 " + str(pid))
            self.lg.info("{} killed".format(name))

        if self.set_of_rules == "CIS" or self.set_of_rules == "CIS-SSS":
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
                p = Process(target=self.run_a_peer, args=[self.splitter_id['address'], "monitor", "M" + str(self.attended_monitors + 0)])
                p.start()
                self.processes["M" + str(self.attended_monitors + 1)] = p.pid
                self.attended_monitors += 1
        elif option == 1:
            if self.attended_peers < self.number_of_peers:
                p = Process(target=self.run_a_peer, args=[self.splitter_id['address'], "peer", "P" + str(self.attended_peers + 1)])
                p.start()
                self.processes["P" + str(self.attended_peers + 1)] = p.pid
                self.attended_peers += 1
        elif option == 2:
            if self.attended_mps < self.number_of_malicious:
                p = Process(target=self.run_a_peer, args=[self.splitter_id['address'], "malicious", "MP" + str(self.attended_mps + 1)])
                p.start()
                self.processes["MP" + str(self.attended_mps + 1)] = p.pid
                self.attended_mps += 1


if __name__ == "__main__":
    #import pdb; pdb.set_trace()
    #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # lg.critical('Critical messages enabled.')
    # lg.error('Error messages enabled.')
    # lg.warning('Warning message enabled.')
    # lg.info('Informative message enabled.')
    # lg.debug('Low-level debug message enabled.')

    fire.Fire(Simulator)

    logging.shutdown()
