from __future__ import print_function
import Pyro4
import threading
import socket

#temp_ip = socket.gethostbyname(socket.gethostname())
HOST_IP = None  # Set accordingly (i.e. "192.168.1.99")
HOST_PORT = None         # Set accordingly (i.e. 9876)


# print(Pyro4.socketutil.getIpAddress())

'''
we have to tell Pyro what parts of the class should be remotely accessible, and what parts aren’t supposed to
be accessible. @Pyro4.expose decorator is used for this purpose.

@Pyro4.behavior(instance_mode="single") => it is required to properly have a persistent Peer inventory

 '''

@Pyro4.expose
class Peer(object):
    def __init__(self):
        # print("> Peer Created.")
        self.vector_timestamp = []
        self.id = 0
        self.v_lock = threading.Lock()
        self.buffer = []
    
    def greeting(self):
        return "Welcome"

    def testing(self):
        m = "No blocking"
        # m = input(">Server\n", )
        print(">Server result : +++ ", m)
        return m

    # neighbs will call this method to send me the message
    def postMessage(self,message,vs,ids):
        if self.checkRecv(vs,self.vector_timestamp,ids):
            
            with self.v_lock:
                self.vector_timestamp = vs            
            
            print(">{0},<{1}>,<{2}>".format(message,self.vector_timestamp,ids))
            self.updateBuffer()
        else:
            print("<Debug buffered: {0},{1},{2}>".format(message,vs,ids))
            self.buffer.append((message,vs,ids))

    def incrementTimeStamp(self):
        with self.v_lock:
            self.vector_timestamp[self.id] += 1

    def updateBuffer(self): # vr means here your own timestamp
        temp_buffer = []
        for i in range(0, len(self.buffer)):
            message,vs,ids = self.buffer[i]
            if self.checkRecv(vs,self.vector_timestamp,ids):
                with self.v_lock:
                    self.vector_timestamp = vs            
                print(">Was Buffered:{0},<{1}>,<{2}>".format(message,self.vector_timestamp,ids))
            else:
                temp_buffer.append((message,vs,ids))

        self.buffer = temp_buffer
        print("<Debug: Updated Buffer>", self.buffer)


    def checkRecv(self, vs, vr, ids):
        def compare(vs,vr,id):
            for i in range(0,len(vr)):
                if i != id:
                    if vs[i] > vr[i]:
                        return False

            return True  

        if vr[ids]+1 == vs[ids] and compare(vs,vr,ids):
            return True
        else:
            return False

   # ============================== Client Handling ==================
def getNeighboursURI(fname,server_peer):  
    content = []
    peers_list = [] 
    ip = socket.gethostbyname(socket.gethostname())
    port = None
    with open(fname) as f:
        content = f.readlines()
    
    content = [x.strip() for x in content]
    i = 0
    for addr in content:
        server_peer.vector_timestamp.append(0)
        if ip in addr:
           server_peer.id = i 
           port = int(addr.split(":")[1])
           continue
        peers_list.append("PYRO:peer@"+addr)
        i += 1
    return (ip,port,peers_list)

def broadCast(server_peer,m,peers,ip,port):
    server_peer.incrementTimeStamp() # increment timestap by one before broadcast
    for peer in peers:
        m = "{0}/{1} says: {2}".format(ip,port,m)
        peer.postMessage(m,server_peer.vector_timestamp,server_peer.id)

    server_peer.updateBuffer()

def handleClient(server_peer,neighbour_uris,h_ip,h_port):
    FLAG = False
    neig_peers = []
    #print(neighbour_uris)
    while True:
        m = input()
        if FLAG == False:
            FLAG = True
            for uri in neighbour_uris:
                neig_peer = Pyro4.Proxy(uri)
                neig_peers.append(neig_peer)
        
        broadCast(server_peer,m,neig_peers,h_ip,h_port)
        

def main1():
    HOST_IP,HOST_PORT,peers = getNeighboursURI("ip.txt")
    SERVER_PEER = Peer()
    args_tuple = (SERVER_PEER,peers,HOST_IP,HOST_PORT)
    t = threading.Thread(target=handleClient, args=args_tuple)
    t.start()

    Pyro4.Daemon.serveSimple(
        {
            SERVER_PEER: "peer"
        },
        ns=False,host=HOST_IP,port= HOST_PORT)
    

if __name__ == "__main__": 
   # ip,port,peers=getNeighboursURI(fname="ip.txt")
   # print(ip,port,peers)
    main1()