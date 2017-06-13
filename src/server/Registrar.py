import socket
import time
import pickle
import paramiko
import threading
import queue
import selectors

from src.server.SSHServer import SSHServer
from src.server.Client import Client
from src.common.EventHandler import FileSystemEventHandler
from src.server.Responder import Responder

"""
== Functionality ==
Index:
    Dictionary of (path, [keys]) where path is a path to be watched and [keys] is a list of SelectorKey objects
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

== Message specification ==
= Client =
Watch:
    Request that the server watch a list of paths. Can be used to alter already watched directory lists.
    {
        'action' : 'watch'
        'path' : [list of directories the server should watch]
    }
Change:
    Request to change file or directory
    {
        'action' : 'modify'
        'path' : path
    }
Changed:
    Notification to the server that client has finished modifying remote file
    {
        'action' : 'modified'
        'path' : path
    }
= Server =
Watching:
    Response to message Watch from the client indicating which of those paths are now watched and which aren't
    {
        'action' : 'watching'
        'watched' : [list of paths watched for this client]
        'not_watched' : [list of paths that failed to be watched]
    }
CanChange:
    Response to message Change. Notification that the client is allowed to modify file on server
    {
        'action' : 'modify_allowed'
        'path' : path
    }
Pull:
    Notification to client that a certain file was changed and the client should update his version
    {
        'action' : 'pull'
        'path' : path
    }
"""

class ParamikoServer(paramiko.ServerInterface):
    def __init__(self, authorized_keys_filename):
        self.authorized_keys_filename = authorized_keys_filename
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        print('[Server] Auth attempt with key: ' + str(key.get_base64()))

        authorized_keys = open(self.authorized_keys_filename, "r")
        lines = authorized_keys.readlines()
        authorized_keys.close()

        for line in lines:
            print("[Server] Comparing "+line+" to "+key.get_base64())
            if key.get_base64() in line and username in line:
                print("[Server] Valid key")
                return paramiko.AUTH_SUCCESSFUL
        print("[Server] Invalid key")
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return 'gssapi-keyex,gssapi-with-mic,password,publickey'

class Registrar(threading.Thread):
    def __init__(self, host, port, server_key, authorized_keys, incoming=None):
        threading.Thread.__init__(self)
        self.server_socket = self.create_socket(host, port)
        self.incoming = (incoming if incoming else queue.Queue())
        self.private_key = paramiko.RSAKey(filename=server_key)
        self.authorized_keys = authorized_keys
        self.selector = selectors.DefaultSelector()
        self.stop_event = threading.Event()
        self.responder = Responder(self.incoming)

    def get_incoming(self):
        return self.incoming

    def run(self):
        num_comm = 0
        self.server_socket.listen(10)
        self.selector.register(self.server_socket, selectors.EVENT_READ)
        print("[Server] All set, listening for SSH connections...")

        while not self.stop_event.is_set():
            events = self.selector.select(timeout=1)
            print('Events: '+str(events))

            # Handle incoming registrations, messages and disconnects
            for key,event in events:
                channel = key.fileobj
                # 1 - New registration
                if channel is self.server_socket:
                    client_socket, address = self.server_socket.accept()
                    client_channel = self.negotiate_channel(client_socket)
                    if not client_channel:
                        continue
                    print("[Server] Now have secure channel with " + str(address))
                    self.selector.register(client_channel, selectors.EVENT_READ, data={})
                else:
                    try:

                        databin = channel.recv(1024 ^ 2)
                        # 2 - Client disconnection
                        if not databin:
                            print("[Server] Disconnection")
                            self.selector.unregister(channel)
                        # 3 - Client message
                        else:
                            num_comm += 1
                            data = pickle.loads(databin)
                            self.incoming.put({
                                'channel': channel,
                                'data': data,
                                'num' : num_comm
                            })
                            print("Server received: " + str(data))
                    except socket.error:
                        self.selector.unregister(channel)

    def negotiate_channel(self, client_socket):
        handler = paramiko.Transport(client_socket)
        handler.add_server_key(self.private_key)
        paramiko_server = ParamikoServer(self.authorized_keys)
        handler.start_server(server=paramiko_server)
        return handler.accept(20)

    def create_socket(self, address, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #server_socket.listen(100)
        server_socket.bind((address, port))
        return server_socket

    def register_directories(self, channel, directories):
        pass

    def stop(self):
        self.stop_event.set()
        self.responder.stop()

if __name__ == '__main__':
    from src.server.Responder import Responder
    server_key_filename = "/home/francisco/.ssh/id_rsa"
    authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"
    print('Let\'s start...')
    incoming = queue.Queue()
    server = Registrar('localhost', 3509, server_key_filename, authorized_keys_filename, incoming)
    server.start()
    while True:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            server.stop()