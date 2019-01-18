"""
@package simulator
peer_ims_simulator module
"""
from core.peer_dbs_simulator import Peer_DBS_simulator
from core.peer_ims import Peer_IMS


class Peer_IMS_simulator(Peer_IMS, Peer_DBS_simulator):
    pass
    #def process_hello(self, sender):
    #    Peer_IMS.process_hello(self, sender)
