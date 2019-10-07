#!/home/vruiz/.pyenv/shims/python -i

import logging
import os
import platform
import time
from glob import glob
from multiprocessing import Manager, Process, Queue
import fire
import numpy as np
import sys
import colorama

from core.monitor_dbs_simulator import Monitor_DBS_simulator
from core.monitor_dbs2_simulator import Monitor_DBS2_simulator
from core.monitor_ims_simulator import Monitor_IMS_simulator
from core.peer_dbs_simulator import Peer_DBS_simulator
from core.peer_dbs2_simulator import Peer_DBS2_simulator
from core.peer_ims_simulator import Peer_IMS_simulator
from core.peer_dbs2_faulty import Peer_DBS2_faulty as Peer_faulty
from core.simulator_stuff import Simulator_stuff as sim
from core.splitter_dbs_simulator import Splitter_DBS_simulator
import core.stderr as stderr

class Simulator():
    P_in  = 0.1  # 0.4 # Churn probability
    
    P_MoP = 0.0  # 0.2 # Monitor probability (apart from the first one)
    P_WIP = 0.5  # 0.6 # 
    P_FP  = 0.5  # 0.2

    def __init__(self, drawing_log="/tmp/drawing_log.txt",
                 set_of_rules="DBS2",
                 number_of_monitors=1,
                 number_of_peers=7,    # Monitor apart
                 number_of_rounds=100,
                 number_of_faulty=0,
                 buffer_size=32,
                 chunk_cadence=0.01,
                 max_chunk_loss_at_peers = 10, # chunks/secon
                 max_chunk_loss_at_splitter = 16,
                 speed = 1000.0,
                 gui=False):

        #logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        if __debug__:
            self.lg.setLevel(logging.DEBUG)
        else:
            self.lg.setLevel(logging.ERROR)

        self.set_of_rules = set_of_rules
        self.number_of_peers = int(number_of_peers)
        self.number_of_monitors = int(number_of_monitors)
        self.drawing_log = drawing_log
        self.number_of_rounds = int(number_of_rounds)
        self.number_of_faulty = number_of_faulty
        self.buffer_size = int(buffer_size)
        self.max_chunk_loss_at_peers = int(max_chunk_loss_at_peers)
        self.max_chunk_loss_at_splitter = float(max_chunk_loss_at_splitter)
        self.current_round = 0
        self.speed = float(speed)
        self.gui = gui
        self.processes = {}

        self.lg.debug(f"set_of_rules=\"{self.set_of_rules}\"")
        stderr.write(f"set_of_rules=\"{self.set_of_rules}\"\n")
        self.lg.debug(f"number_of_peers={self.number_of_peers}")
        stderr.write(f"number_of_peers={self.number_of_peers}\n")
        self.lg.debug(f"number_of_monitors={self.number_of_monitors}")
        stderr.write(f"number_of_monitors={self.number_of_monitors}\n")
        self.lg.debug(f"number_of_rounds={self.number_of_rounds}")
        stderr.write(f"number_of_rounds={self.number_of_rounds}\n")
        self.lg.debug(f"number_of_faulty={self.number_of_faulty}")
        stderr.write(f"number_of_faulty={self.number_of_faulty}\n")
        self.lg.debug(f"buffer_size={self.buffer_size}")
        stderr.write(f"buffer_size={self.buffer_size}\n")
        self.lg.debug(f"max_chunk_loss_at_peers={self.max_chunk_loss_at_peers}")
        stderr.write(f"simulator: max_chunk_loss_at_peers={self.max_chunk_loss_at_peers}\n")
        self.lg.debug(f"max_chunk_loss_at_splitter={self.max_chunk_loss_at_splitter}")
        stderr.write(f"max_chunk_loss_at_splitter={self.max_chunk_loss_at_splitter}\n")
        self.lg.debug(f"speed={self.speed}")
        stderr.write(f"speed={self.speed}\n")

        stderr.write(f"CPU usage\n")
        stderr.write(f"{colorama.Fore.MAGENTA}Team size{colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Fore.RED}Lost chunk{colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Fore.RED}(Unsupportive peer){colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Fore.BLUE}Deleted peer{colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Fore.YELLOW}Round{colorama.Style.RESET_ALL}\n")
        if __debug__:
            stderr.write(f"{colorama.Back.RED}{colorama.Fore.BLACK}Max hops{colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Back.CYAN}{colorama.Fore.BLACK}Requested chunk{colorama.Style.RESET_ALL}\n")
        stderr.write(f"{colorama.Fore.CYAN}Prunned chunk{colorama.Style.RESET_ALL}\n")

    def compute_team_size(self, n):
        return 2 ** (n - 1).bit_length()

    def compute_buffer_size(self):
        # return self.number_of_monitors + self.number_of_peers + self.number_of_faulty
        team_size = self.compute_team_size((self.number_of_monitors + self.number_of_peers + self.number_of_faulty) * 8)
        if (team_size < 32):
            return 32
        else:
            return team_size

    def run_a_splitter(self, splitter_id):
        if self.buffer_size == 0:
            self.buffer_size = self.compute_buffer_size()
        if self.set_of_rules == "DBS" or self.set_of_rules == "DBS2" or self.set_of_rules == "IMS":
            splitter = Splitter_DBS_simulator(
                buffer_size = self.buffer_size,
                max_chunk_loss = self.max_chunk_loss_at_splitter,
                number_of_rounds = self.number_of_rounds,
                speed = self.speed)
            self.lg.debug("simulator: DBS/IMS splitter created")

        # splitter.start()
        splitter.setup_peer_connection_socket()
        splitter.setup_team_socket()
        splitter_id['address'] = splitter.get_id()
        splitter.max_number_of_rounds = self.number_of_rounds
        splitter.run()

    def run_a_peer(self, splitter_id, type, id, first_monitor=False):
        total_peers = self.number_of_monitors + self.number_of_peers + self.number_of_faulty
        chunks_before_leave = np.random.weibull(2) * (total_peers * (self.number_of_rounds - self.current_round))
        self.lg.debug("simulator: creating {}".format(type))
        if type == "monitor":
            if first_monitor is True:
                pass
                #chunks_before_leave = 99999999
            if self.set_of_rules == "DBS":
                peer = Monitor_DBS_simulator(id = id,
                                             name = "Monitor_DBS_simulator")
                self.lg.debug("simulator: DBS monitor created")
            elif self.set_of_rules == "IMS":
                peer = Monitor_IMS_simulator(id = id,
                                             name = "Monitor_IMS_simulator")
                self.lg.debug("simulator: IMS monitor created")
            elif self.set_of_rules == "DBS2":
                peer = Monitor_DBS2_simulator(id = id,
                                             name = "Monitor_DBS2_simulator")
                self.lg.debug("simulator: DBS2 monitor created")
        elif type == "faulty":
            peer = Peer_faulty(id, name="Peer_DBS2_faulty")
            self.lg.debug("simulator: faulty peer created")
        else:
            if self.set_of_rules == "DBS":
                peer = Peer_DBS_simulator(id = id, name = "Peer_DBS_simulator")
                self.lg.debug("simulator: DBS peer created")
            elif self.set_of_rules == "DBS2":
                peer = Peer_DBS2_simulator(id = id, name = "Peer_DBS2_simulator")
                self.lg.debug("simulator: DBS2 peer created")
            elif self.set_of_rules == "IMS":
                peer = Peer_IMS_simulator(id = id, name = "Peer_IMS_simulator")
                self.lg.debug("simulator: IMS peer created")
        self.lg.debug("simulator: {}: alive till consuming {} chunks".format(id, chunks_before_leave))

        #peer.chunks_before_leave = chunks_before_leave
        peer.set_splitter(splitter_id)
        if peer.connect_to_the_splitter(peer_port=0):
            peer.receive_the_public_endpoint()
            peer.receive_the_peer_index_in_team()
            peer.receive_the_number_of_peers()
            peer.listen_to_the_team()
            peer.receive_the_list_of_peers()
            if isinstance(peer, Peer_faulty):
                peer.choose_target()
            peer.receive_the_buffer_size()
            peer.receive_the_chunk_size()
            #peer.send_ready_for_receiving_chunks()
            #peer.send_peer_type()   #Only for simulation purpose
            # peer.buffer_data()
            # peer.start()
            peer.run()

        '''
        while not peer.ready_to_leave_the_team:
            if type != "faulty" and peer.number_of_chunks_consumed >= chunks_before_leave and peer.player_alive:
                self.lg.debug("simulator:", id, "reached the number of chunks consumed before leave", peer.number_of_chunks_consumed)
                peer.player_alive = False
            time.sleep(1)
        '''
        self.lg.debug("simulator: {}: left the team".format(id))

    def store(self):
        """Create a log file for drawing
        """
        drawing_log_file = open(self.drawing_log, "w", 1)

        # Configuration in the first line
        m = ["C", self.number_of_monitors, self.number_of_peers, self.number_of_faulty, self.number_of_rounds, self.set_of_rules]
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
        self.lg.debug("CLOSING STORE")
        drawing_log_file.close()

    def addPeer(self):
        probabilities = [Simulator.P_MoP, Simulator.P_WIP, Simulator.P_FP]
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
            if self.attended_faulty_peers < self.number_of_faulty:
                p = Process(target=self.run_a_peer, args=[self.splitter_id['address'], "faulty", "F" + str(self.attended_faulty_peers + 1)])
                p.start()
                self.processes["F" + str(self.attended_faulty_peers + 1)] = p.pid
                self.attended_faulty_peers += 1

    def run(self):
        self.lg.debug("simulator: platform.system()={}".format(platform.system()))
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

        # Create shared list for CIS set of rules (only when cis is choosen?)
        manager = Manager()
        sim.SHARED_LIST["faulty"] = manager.list()
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
        self.attended_faulty_peers = 0

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
                if (r <= Simulator.P_in) and (self.current_round < self.number_of_rounds):
                    self.addPeer()
            m = queue.get()

        sim.FEEDBACK["DRAW"].put(("Bye", "Bye"))
        sim.FEEDBACK["STATUS"].put(("Bye", "Bye"))
        for name, pid in self.processes.items():
            self.lg.debug("Killing {}, ...".format(name))
            os.system("kill -9 " + str(pid))
            self.lg.debug("{} killed".format(name))
        stderr.write("\n");

if __name__ == "__main__":
    fire.Fire(Simulator)
    logging.shutdown()
