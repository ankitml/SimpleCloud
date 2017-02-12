import os, threading, pickle, socket
from paramiko import Channel

class Client(Channel):
    def __init__(self, address, socket, directories):
        super(Client, self).__init__(socket)
        self._address = address
        self._socket = socket
        self._directories = directories
        self._watches = []
        self._lock = threading.Lock()

    def sendall(self, message):
        message_b = pickle.dumps(message)
        try:
            #self.socket.send(message_b)
            self.sendall(message_b)
        except (socket.error, EOFError) as err:
            return False
        return True

    def __getattr__(self, item):
        return getattr(self._socket, item)

    def addWatches(self, watches):
        self.watches.extend(watches)

    def isWatching(self, path):
        for directory in self.directories:
            if directory.startswith(path):
                return True
        return False