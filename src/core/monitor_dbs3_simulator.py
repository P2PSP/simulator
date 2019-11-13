"""
@package simulator
monitor_dbs3_simulator module
"""

#from .monitor_dbs2_simulator import Monitor_DBS2_simulator
#from .peer_dbs3 import Peer_DBS3
from .monitor_dbs3 import Monitor_DBS3
from .peer_simulator import Peer_simulator

#class Monitor_DBS3_simulator(Monitor_DBS2_simulator, Peer_DBS3):
class Monitor_DBS3_simulator(Monitor_DBS3, Peer_simulator):

    def __init__(self, id, name = "Monitor_DBS3_simulator"):
        Monitor_DBS3.__init__(self)
        Peer_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: initialized")
