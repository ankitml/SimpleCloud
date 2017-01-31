import threading, socket, paramiko, pickle
from src.server.SSHServer import SSHServer

class ClientRegistrar(threading.Thread):
    def __init__(self, host, port, client_queue, server_key_rsa, authorized_keys):
        self.host = host
        self.port = port
        self.clients = client_queue
        self.SOCKET_NBYTES = 1024*1024 # Read at most 1MB from the server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', 3509))
        server_socket.listen()
        self.server_socket = server_socket
        self.server_key = paramiko.RSAKey(server_key_rsa)
        self.authorized_keys = authorized_keys

    def run(self):
        while True:
            # Await for client to connect
            print("[Client Registrator] All set, listening for SSH connections...")
            client_socket, address = self.server_socket.accept()

            # Create SSH tunnel
            print("[Client Registrator] Received client connection from " + str(address))
            server = paramiko.Transport(client_socket)
            server.add_server_key(self.server_key)
            print("[Client Registrator] ("+address+") Instantiating Paramiko server")
            ssh_handler = SSHServer(self.authorized_keys)
            print("[Client Registrator] ("+address+") Authentication worked")
            server.start_server(server=ssh_handler)
            channel = server.accept(20)
            if not channel:
                continue

            # Obtain a serialized list of directories that the client wants to watch and
            # insert it into the registry, along with the channel
            sync_dirs_b = channel.recv(self.SOCKET_NBYTES)
            if not sync_dirs_b:
                print("[Server] ("+address+") Socket closed")
            sync_dirs = pickle.loads(sync_dirs_b)
            client_info = { "address" : address, "channel" : socket, "directories" : sync_dirs }
            print("[Server] ("+address+") Inserting client info into registry: "+str(client_info))
            self.clients.put(client_info)