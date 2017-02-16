import selectors, threading, time, queue, socket
import asyncio
import paramiko
from src.server.SSHServer import SSHServer
from tests.SSHCommunication import Client, Server

# This test will create server-side a thread to handle a server socket for registration
# and a thread to handle registered client sockets
# The server socket has a Selector for reading the server socket and the several client sockets
# When the handler thread receives a disconnect, it should remove that socket from the
# server thread's selector

class ServerThread(threading.Thread):
    class SSHProtocol(asyncio.Protocol):
        server_key = paramiko.RSAKey(filename="/home/francisco/.ssh/id_rsa")
        authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"
        def __init__(self, loop):
            self.loop = loop
            self.client_address = None
        def connection_made(self, transport):
            self.client_address = str(transport.get_extra_info("peername"))
            print("[SSH Server] connected to "+self.client_address)
            ssh_transport = paramiko.Transport(transport) # create an SSH transport
            ssh_transport.add_server_key(self.server_key) # add a private key to it
            paramikoServer = SSHServer(self.authorized_keys_filename) # create a Paramiko handler
            ssh_transport.start_server(paramikoServer) # start a paramiko transport
            self.channel = ssh_transport.accept()

        def connection_lost(self, exc):
            print("[SSH Server] lost connection to "+self.client_address)

        def data_received(self, data):
            if not data:
                self.connection_lost(None)
            print("[SSH Server] received \'"+str(data)+"\' from "+self.client_address)
            self.channel

    def __init__(self, host, port):
        super(ServerThread, self).__init__()
        self.loop = asyncio.get_event_loop()
        self.server = self.loop.create_server(self.ServerProtocol, host=host, port=port)
    def run(self):
        self.loop.run_until_complete(self.server) # Check for bad things
        try:
            self.loop.run_forever() # Actually listen
        finally:
            self.loop.close()



#def handlerRoutine(serverQueue):
#def clientRoutine():
server = ServerThread("localhost", 3509)
server.start()

#serverQueue = queue.Queue()
#handlerThread = threading.Thread(target=handlerRoutine, args=[serverQueue])