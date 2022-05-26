import socket
import netifaces
from _thread import *

from threading import RLock

import json
import time
from pythonping import ping

#semaphore allows editing the global vectors dict
LOCK = RLock()

hostname = socket.gethostname().split(".")[0]
port = 1233
ThreadCount = 0

#host => [cost, nextHop]
VECTORS = {
    hostname: [0, None]
}

def print_vectors(vectors):
    """ Given a vector list, prints it in matrix form. """
    adj_width = 34
    nodes = [v for v in vectors]
    vecs = [str(vectors[v]) for v in vectors]
    lens = [max(len(nodes[i]), len(vecs[i])) for i in range(len(nodes))]
    header = "|" + "|".join([nodes[i].ljust(lens[i], ' ') for i in range(len(nodes))]) + "|"
    print ("-" * len(header))
    print(header)
    print ("-" * len(header))
    print("|" + "|".join([vecs[i].ljust(lens[i], ' ') for i in range(len(nodes))]) + "|")
    print ("-" * len(header))
    print("\n")

def send_update(host, message):
    """ Sends update to other servers. """
    # message will be in form [hostname, edge_len, vectors]
    ClientSocket = socket.socket()
    try:
        ClientSocket.connect((host, port))
        ClientSocket.send(str.encode(message))
        Response = ClientSocket.recv(2048)
        #print(Response.decode('utf-8'))
        ClientSocket.close()
    except socket.error as e:
        #print(str(e))
        pass
    #Response = ClientSocket.recv(2048)
    


def update_vectors(connection, address):
    """ When new vectors are sent from another, update the local vectors."""
    #connection.send(str.encode('You are now connected to the replay server... Type BYE to stop'))
    #while True:
    data = connection.recv(2048)
    message = data.decode('utf-8')
    with LOCK:
        source, dist, vectors = json.loads(message)
        # Add the neighbors to vectors if communication is booting
        updates_made = False
        for v in vectors:
            new_dist = round(dist + vectors[v][0], 2)
            new_hop = [source] + (list(vectors[v][1]) if vectors[v][1] else [])
            if VECTORS.setdefault(v, (float('inf'), None)) > [new_dist, new_hop]:
                VECTORS[v] = [new_dist, new_hop]
                updates_made = True
        if updates_made:
            print("Recieved DV table from", source)
            print_vectors(vectors)
            print("New Local Table")
            print_vectors(VECTORS)
        # if updates_made:
        #     send_update(address, json.dumps(VECTORS))
        pass #update vectors
    #reply = f'Server: {message}'
    connection.send(str.encode("RECIEVED"))
    connection.close()

def accept_connections(ServerSocket):
    """ If there is a connection, start a new thread to handle it """
    client, address = ServerSocket.accept()
    #print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(update_vectors, (client, address[0], ))

def recieve_updates(port):
    """ Start listening on the given host & port. Accept any connections offered."""
    ServerSocket = socket.socket()
    try:
        ServerSocket.bind(('0.0.0.0', port))
    except socket.error as e:
        #print(str(e))
        pass
    #print(f'Server is listing on the port {port}...')
    ServerSocket.listen()
    while True:
        accept_connections(ServerSocket)

def run(port):
    """ Sets up a listening thread and sends out periodic updates. """
    start_new_thread(recieve_updates, (port, ))
    while True:
        print_vectors(VECTORS)
        # simple lambda to flip the interface to get the connected ip
        flip_ip = lambda i: ".".join(i.split(".")[:-1] + ["1" if i.split(".")[-1] == "2" else "2"])
        # ip, ping_time
        neighbors = [(flip_ip(i), ping(flip_ip(i), count=5).rtt_avg) for i in [netifaces.ifaddresses(str(i))[2][0]['addr'] for i in netifaces.interfaces() if i not in ["lo", "eth0"]]]
        for neighbor, dist in neighbors:
            start_new_thread(send_update, (neighbor, json.dumps([hostname, round(100 * dist, 2), VECTORS]), ))
        time.sleep(10)

run(port)
