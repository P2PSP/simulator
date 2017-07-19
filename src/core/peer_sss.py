"""
@package simulator
peer_sss module
"""
from .peer_strpeds import Peer_STRPEDS
from .simulator_stuff import Simulator_stuff as sim

class Peer_SSS(Peer_STRPEDS):

    def __init__(self, id):
        self.first_round = 0
        super().__init__(id)

        # --------- For simulation purposes only ------------
        # To do shamir secret sharing instead of using this
        self.t = {}
        self.splitter_t = {}
        # ---------------------------------------------------

        print("Peer SSS initialized")

    def get_my_secret_key(self, shares):
        # Not needed for simulation
        return NotImplementedError

    # ----------- simulation purposes ----------
    def polite_farewell(self):
        print(self.id, ": (see you later)")
      
        for peer in self.peer_list:
            self.say_goodbye(peer)

        del sim.RECV_LIST[self.id]
        self.ready_to_leave_the_team = True
        print(self.id, ": ready to leave the team")
    # -------------------------------------------

    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print(self.id, "Sender is in the bad peer list", sender)
            return -1

        if sender == self.splitter or self.check_message(message, sender):
            if self.is_a_control_message(message) and message[1] == "S":
                return self.handle_bad_peers_request()
            else:
                if self.is_a_control_message(message):
                    return self.process_message_burst(message, sender)
                else:
                    current_round = message[2]
                    if (current_round in self.t):
                        self.t[current_round] += 1
                    else:
                        self.t[current_round] = 1

                    self.splitter_t[current_round] = message[3]

                    print(self.id, "current_round", current_round)

                    if ((current_round-1) in self.t):
                        print(self.id, "t", self.t[(current_round-1)], "splitter_t", self.splitter_t[(current_round-1)])
                        print(self.id, "this.t", self.t[(current_round)], "this.splitter_t", self.splitter_t[(current_round)])

                    return self.process_message_burst(message, sender)

        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    def send_chunk(self, peer):
        encrypted_chunk = (self.receive_and_feed_previous[0], "B", self.receive_and_feed_previous[2], self.receive_and_feed_previous[3])
        current_round = self.receive_and_feed_previous[2]
        if ((current_round-1) in self.t) and (self.first_round != (current_round-1)):
            if self.t[(current_round-1)] >= self.splitter_t[(current_round-1)]:
                self.sendto(self.receive_and_feed_previous, peer)
                self.sendto_counter += 1
            else:
                print("###########=================>>>>", self.id, "Need more shares, I had", self.t[(current_round-1)], "from", self.splitter_t[(current_round-1)], "needed")
                self.sendto(encrypted_chunk, peer)
                self.sendto_counter += 1
        else:
            if (current_round-1) == self.first_round:
                print(self.id, "I cant get enough shares in my first round")
            else:
                print(self.id, "is my first round")
                self.first_round = current_round
            self.sendto(self.receive_and_feed_previous, peer)
            self.sendto_counter += 1

    def process_message_burst(self, message, sender):
        # ----- Only for simulation purposes ------
        # ----- Check if new round for peer -------
        if not self.is_a_control_message(message) and sender == self.splitter:
            if self.played > 0 and self.played >= len(self.peer_list):
                clr = self.losses/self.played
                sim.FEEDBACK["DRAW"].put(("CLR", self.id, clr))
                self.losses = 0
                self.played = 0
        # ------------------------------------------

        if (message[0] >= 0):
            chunk_number = message[0]
            chunk = message[1]

            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)

            # --- for simulation purposes only ----
            self.sender_of_chunks[chunk_number % self.buffer_size] = sender

            chunks = ""
            for n, c in self.chunks:
                chunks += c
                if c == "L":
                    self.sender_of_chunks[n % self.buffer_size] = ""

            sim.FEEDBACK["DRAW"].put(("B", self.id, chunks,":".join(self.sender_of_chunks)))
            # --------------------------------------

            self.received_counter += 1
            if (sender == self.splitter):
                while(self.receive_and_feed_counter < len(self.peer_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]
                    self.receive_and_feed_previous = message

                    self.send_chunk(peer)
                    self.debt[peer] += 1

                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print(self.id, ":", peer, "removed by unsupportive (", str(self.debt[peer]), "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "OUT", self.id, peer))
                    else:
                        self.receive_and_feed_counter += 1

                # Modifying the first chunk to play (it increases the delay)
                #if (not self.receive_and_feed_previous):
                    #self.played_chunk = message[0]
                    #print(self.id,"First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                self.receive_and_feed_counter = 0

            else:

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by chunk", chunk_number)
                    print(self.id, ":", "peer_list =", self.peer_list)
                    # -------- For simulation purposes only -----------
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender))
                    # -------------------------------------------------

                else:
                    self.debt[sender] -= 1

            # ----------- simulation purposes ---------
            if self.id.find("MP") == -1:
                sim.RECV_LIST[self.id] = chunk_number
            # ----------------------------------------
            
            return chunk_number

        else:
            # A control chunk has been received
            if __debug__:
                print(self.id, ": control message received:", message)

            if message[1] == "H":
                if sender not in self.peer_list:
                    self.sendto((-1, 'H'), sender)
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by [hello]")
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
            else:
                if sender in self.peer_list:
                    print(self.id, ": received goodbye from", sender)
                    try:
                        self.peer_list.remove(sender)
                        print(self.id, ":", sender, "removed from peer_list")
                    except:
                        print(self.id, ": failed to remove peer", sender, "from peer_list", self.peer_list)
                        
                    del self.debt[sender]
                    
                if sender in self.neighborhood:
                    if (self.receive_and_feed_counter > 0):
                        self.modified_list = True
                        self.receive_and_feed_counter -= 1
                    try:
                        self.neighborhood.remove(sender)
                    except:
                        print(self.id, ": failed to remove peer", sender, "from neighborhood", self.neighborhood)

                    print(self.id, ":", "peer_list =", self.peer_list)
                    print(self.id, ":", "neighborhood =", self.neighborhood)

                else:
                    if (sender == self.splitter):
                        print(self.id, ": received goodbye from splitter")
                        self.waiting_for_goodbye = False
            return -1
