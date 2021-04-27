###
# File: client.py
# Created: 03/29/2021
# Author: Jordan Williams (jwilliams13@umassd.edu)
# -----
# Last Modified: 04/27/2021
# Modified By: Jordan Williams
###

# Common dependencies
from distributed_common import *

# Packages
import datetime
import pandas as pd
from io import StringIO

# Modules
import simulation as sim

OUTPUT_PATH = './output/data/distributed/'

class Client():
    def __init__(self):
        self.sckt = get_socket()
        self.sckt.connect(ADDR)

        self.next_pid = 0

        self.loop = True

        self.queue = []         # packets waiting to be sent
        self.sent_packets = {}  # sent packets waiting for acknowledgement

        # Initialize receiver thread
        self.receiver = threading.Thread(
            target = self.receive,
            #daemon=True
        )
        self.receiver.start()
    
    def next_request(self):
        if(len(self.queue) != 0):
            # Send next request in queue
            self.send(self.queue.pop(0))

        # Only send disconnect message after all acknowledgements are received
        #elif(len(self.sent_packets) == 0):
        #    self.request(DISCONNECT_MESSAGE)

    def send(self, params, pid = None):
        if(pid is None):
            packet_id = self.next_pid
            self.next_pid = (self.next_pid + 1) % MAX_PID   # wrap next packet ID
        else:
            packet_id = pid


        # Only require an acknowledgement if this is NOT an acknowledgement itself
        if(params != 'acknowledged'):
            self.sent_packets[packet_id] = params   # add this to list of packets which need confirmation

        full_packet = generate_packet(packet_id, 'client', params)
        self.sckt.send(full_packet)

    def acknowledge(self, pid):
        ret = None
        try:
            if(self.sent_packets.get(pid) == DISCONNECT_MESSAGE):
                ret = False

            log.info(f"ACK recv.: pid:{pid} ({self.sent_packets[pid][:30]})")
            del self.sent_packets[pid]
        except:
            log.info(f"Received packet acknowledgement for pid:{pid} when we we didn't need it.")

        # Next request
        self.next_request()
        return ret

    def send_acknowledgement(self, pid):
        self.send("acknowledged", pid)
        #log.info("sending acknowledgement (%s)" % packet_id)

    def receive(self):
        while(self.loop):
            pid, packet_type, msg = receive(self.sckt)
            if(msg == 'acknowledged'):
                # Stop thread if we get a disconnect acknowledgment
                if(self.acknowledge(pid) == False):
                    break
            else:
                self.handle_simulation_data(msg)
                self.send_acknowledgement(pid)

                # Close connection
                self.loop = False

    def handle_simulation_data(self, data):
        # Read string to dataframe
        df = pd.read_csv(StringIO(data))

        time = datetime.datetime.now().strftime('%Y-%m-%dT%H%M%S')
        # Write data to file
        df.to_csv(OUTPUT_PATH + '%s.csv' % (time), mode = 'a', index=False)

def main():
    client = Client()

    # Read params from config file
    fp = open('./config/simulation/distributed.json')
    params = json.dumps(json.load(fp))

    # Add new simulation request to queue
    client.queue.append(params)

    # Send max of `MAX_PID // 2` requests at once
    for _ in range(MAX_PID // 2):
        # Stop early if needed
        if(len(client.queue) == 0):
            break
        client.next_request()

if __name__ == '__main__':
    main()