#!/home/vruiz/.pyenv/shims/python -i

from simulator import Simulator
from core.splitter_dbs_latency import Splitter_DBS_latency as Splitter_DBS
from core.peer_dbs_latency import Peer_DBS_latency as Peer_DBS
from core.monitor_dbs_latency import Monitor_DBS_latency as Monitor_DBS
from core.common import Common

import fire
import numpy as np

class Simulator_with_latency(Simulator):
    def run_a_splitter(self,splitter_id):
        Common.CHUNK_CADENCE = self.chunk_cadence
        if self.buffer_size == 0:
            Common.BUFFER_SIZE = self.compute_buffer_size()
        else:
            Common.BUFFER_SIZE = self.buffer_size
        self.lg.debug("(definitive) buffer_size={}".format(Common.BUFFER_SIZE))
        if self.set_of_rules == "DBS" or self.set_of_rules == "IMS":
            splitter = Splitter_DBS()
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
        #while splitter.current_round < self.number_of_rounds:
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
                peer = Monitor_DBS(id, "Monitor_DBS")
                self.lg.info("simulator: DBS monitor created")
            elif self.set_of_rules == "IMS":
                peer = Monitor_IMS(id, "Monitor_IMS")
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
                peer = Peer_DBS(id, "Peer_DBS")
                self.lg.info("simulator: DBS peer created")
            if self.set_of_rules == "IMS":
                peer = Peer_IMS(id, "Peer_IMS")
                self.lg.info("simulator: IMS peer created")
            elif self.set_of_rules == "CIS":
                peer = Peer_STRPEDS(id)
                self.lg.info("simulator: CIS peer created")
            elif self.set_of_rules == "CIS-SSS":
                peer = Peer_SSS(id)
                self.lg.info("simulator: CIS-SSS peer created")
        self.lg.critical("simulator: {}: alive till consuming {} chunks".format(id, chunks_before_leave))

        peer.link_failure_prob = self.link_failure_prob
        peer.max_degree = self.max_degree
        peer.chunks_before_leave = chunks_before_leave
        peer.set_splitter(splitter_id)
        # peer.set_id()
        peer.connect_to_the_splitter()
        peer.receive_buffer_size()
        peer.receive_the_number_of_peers()
        peer.listen_to_the_team()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        peer.send_peer_type()   #Only for simulation purpose
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

fire.Fire(Simulator_with_latency)
