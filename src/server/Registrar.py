import socket
import time
import pickle
import paramiko
import threading
import queue
import selectors

from watchdog.observers import Observer
from src.server.EventHandler import FileSystemEventHandler
from src.server.SSHServer import SSHServer
from src.server.Responder import Responder

from src.server.Index import Index

"""
== Functionality ==
Index:
    Dictionary of (path, [channels]) where path is a path to be watched and [keys] is a list of Paramiko Channel objects
    Property of the Responder
Watching:
    Dictionary of (path, key) where path is a path being watched by a key's client
    Property of the Responder
Registrar:
    Thread responsible for receiving new client connections, listening to their channels for news messages (which
    are inserted into the incoming queue) and noticing disconnects
Responder:
    Thread responsible for receiving messages from the incoming queue and generating an appropriate response which is
    sent into the channel attached to that message, if possible

The Registrar binds a regular TCP socket and awaits connections through a selector. Upon receiving one, a SSH channel
is negotiated and added to the selector's list of reading. The data property of the selector's key will be initialized
with a dictionary
The channel is then supposed to receive a Watch message containing the list of path the client wants to be
watched. First, we consult the Index dictionary (to be defined where it resides) for each received path, and if it is
already watched we simply add a new SelectorKey to the list. If not, the Observer is scheduled to watch those
directories and upon success a new entry is added to the Index in the form of { path:[key] }. Then, the path list will
be appended to the 'watching' key of the data dictionary of the selector key, indicating that client is watching those
directories, which will be useful for when they disconnect. A Watching message is sent containing the successfully
watched paths.
When a disconnect happens, the 'watching' list from the SelectorKey object is matched to the Index dictionary and the
SelectorKey is removed from each SelectorKey list. If the list is empty, the watch for that path is unscheduled. The
SelectorKey's file object gets unscheduled.
When a Change message arrives, a new entry is inserted into a Changing dictionary (to be defined where it resides),
in the form of { path:key } where path is the message's path and key is the SelectorKey object, indicating that path
is being changed by that SelectorKey's client. If an entry for this path OR ANY SUBPATH (ABOVE OR BELOW) exists,
the request to change is denied (maybe send a message saying so?). Otherwise a CanChange message is sent.
"""

class Registrar(threading.Thread):
    def __init__(self, host, port, server_key, authorized_keys, host_keys=None, incoming=None):
        threading.Thread.__init__(self)
        self.server_socket = self.create_socket(host, port)
        self.incoming = (incoming if incoming else queue.Queue())
        self.private_key = paramiko.RSAKey(filename=server_key)
        self.authorized_keys = authorized_keys
        self.host_keys = host_keys
        self.selector = selectors.DefaultSelector()
        self.num_conn = 0
        self.stop_event = threading.Event()
        self.index = Index()
        self.observer = Observer()
        # Server functionality
        self.channels = {}
        self.paramiko_server = SSHServer(self.authorized_keys)
        # Client functionality
        self.clients = []
        self.to_watch = queue.Queue() # ???
        # Responder threads
        handler = FileSystemEventHandler(self.index, self.incoming)
        self.responder = Responder(index=self.index, channels=self.channels, incoming=self.incoming, observer=self.observer, handler=handler)

    def connect(self, host, port):
        client = paramiko.SSHClient()
        client.load_system_host_keys(self.host_keys)
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(host, port=port, pkey=self.private_key)
        # input, output, err = client.exec_command("ls -la")
        # for line in output.readlines():
        #     print(line)
        transport = client.get_transport()
        channel = transport.open_channel(kind="session")
        self.clients.append(client)
        self.to_watch.put(channel)
        return channel

    def get_incoming(self):
        return self.incoming

    def run(self):
        self.server_socket.listen(10)
        self.selector.register(self.server_socket, selectors.EVENT_READ)
        self.responder.start()
        self.observer.start()
        print("[Server] All set, listening for SSH connections.")

        while not self.stop_event.is_set():
            events = self.selector.select(timeout=1)
            #print('Events: '+str(events))

            # 1 - Handle incoming client registrations, messages and disconnects
            for key,event in events:
                channel = key.fileobj
                # 1.1 - New registration
                if channel is self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    client_channel = self.negotiate_channel(client_socket)
                    if not client_channel:
                        continue
                    # Successful negotiation
                    print("[Server] Now have secure channel with " + str(address))
                    self.register_channel(client_channel)
                else:
                    channel_id = key.data["channel_id"]
                    try:
                        databin = channel.recv(1024 ^ 2)
                        # 1.2 - Client disconnection
                        if not databin:
                            print("[Server] Disconnection")
                            self.remove_channel(channel, channel_id)
                        # 1.3 - Client message
                        else:
                            data = pickle.loads(databin)
                            self.incoming.put((
                                "respond",
                                channel_id,
                                data))
                            print("[Server] Received: " + str(data))
                    except socket.error:
                        self.remove_channel(channel, channel_id)

            # 2 - Register connected server channels for observation
            while True:
                try:
                    server_channel = self.to_watch.get(block=False)
                    self.register_channel(server_channel)
                except queue.Empty:
                    break
        print("[Registrar] Stopping")

    def register_channel(self, channel):
        self.num_conn += 1
        self.index.add_channel(self.num_conn)
        self.channels[self.num_conn] = channel
        self.selector.register(channel, selectors.EVENT_READ, data={"channel_id": self.num_conn})
        print("Added channel #"+str(self.num_conn))

    def remove_channel(self, channel, channel_id):
        self.selector.unregister(channel)
        self.index.remove_channel(channel_id)

    def negotiate_channel(self, client_socket):
        handler = paramiko.Transport(client_socket)
        handler.add_server_key(self.private_key)
        handler.start_server(server=self.paramiko_server)
        return handler.accept(20)

    def create_socket(self, address, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #server_socket.listen(100)
        server_socket.bind((address, port))
        return server_socket

    def stop(self):
        self.stop_event.set()
        self.responder.stop()

if __name__ == '__main__':
    server_key_filename = "/home/francisco/.ssh/id_rsa"
    authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"
    print('Let\'s start...')
    #server = Registrar('localhost', 3509, server_key_filename, authorized_keys_filename)
    #server.start()
    while True:
        port_str = input("What is my port?\n> ")
        try:
            port = int(port_str)
            if port not in range(1024, 65535):
                raise ValueError
            break
        except ValueError:
            print("Invalid port number")
    registrar = Registrar('localhost', port, server_key_filename, authorized_keys_filename)
    registrar.start()
    try:
        mode = input("Am I a server or a client? (S\\C)\n> ")
        # Server
        # pass
        # Client
        if mode in ["C", "c"]:
            remote = input("What local port should I connect to? \n> ")
            #split = remote.split(":")
            #host = split[0]
            #port = int(split[1])
            host = "localhost"
            port = int(remote)
            channel = registrar.connect(host, port)
            while True:
                action = input("R - request watch | T - touch /home/francisco/.temp/dir_client/file1\n")
                if action in ["R","r"]:
                    channel_id = list(registrar.channels.keys())[0]
                    registrar.responder.request_watch(
                        [("/home/francisco/.temp/dir_client",
                        "/home/francisco/.temp/dir_server/")],
                        channel_id)
                elif action in ["T","t"]:
                    with open("/home/francisco/.temp/dir_client/file1","w") as myfile:
                        myfile.write("ola")
                time.sleep(0.5)
        else:
            while True:
                time.sleep(10)
    except KeyboardInterrupt:
        registrar.stop()
