from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.splitter_dbs import Splitter_DBS
from threading import Thread
import time

class Simulator:

    def __init__(self, number_of_monitors, number_of_peers):
        self.number_of_peers = number_of_peers
        self.number_of_monitors = number_of_monitors

    def run_a_splitter(self):     
        self.splitter = Splitter_DBS()
        splitter = self.splitter
        splitter.start()
        while splitter.alive:
            time.sleep(1)
            print("Splitter's list of peers:", ', '.join(str(p.id) for p in splitter.peer_list))

    def run_a_peer(self, type, id):
        if type == "monitor":
            peer = Monitor_DBS(id)
        else:
            peer = Peer_DBS(id)
            
        peer.set_splitter(self.splitter)
        peer.connect_to_the_splitter()
        peer.receive_the_number_of_peers()
        peer.receive_the_list_of_peers()
        #peer.send_ready_for_receiving_chunks()
        peer.buffer_data()
        peer.start()

        while peer.player_alive:
            pass
            
    def run(self):
        Thread(target=self.run_a_splitter).start()
        
        for i in range(self.number_of_monitors):
            Thread(target=self.run_a_peer, args=["monitor", "M"+str(i+1)]).start()
        
        for i in range(self.number_of_peers):
            time.sleep(0.5)
            Thread(target=self.run_a_peer, args=["peer", "P"+str(i+1)]).start()
        

if __name__ == "__main__":
    app = Simulator(1,5)
    app.run()
    
