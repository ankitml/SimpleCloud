import threading
import selectors

class ClientIndex(threading.Thread):
    def __init__(self):
        super(ClientIndex, self).__init__()
        self.lock = threading.Lock()
        #self.clients = []
        self.selector = selectors.DefaultSelector()
        self.client_id = 0

    def run(self):
        while True:
            readables,_,_ = self.clients

    def put(self, client):
        client[ "lock" ] = threading.Lock
        self.lock.acquire()
        self.client_id += 1
        self.clients[ self.client_id ] = client
        self.lock.release()
        return self.client_id

    def get(self, client_id):
        #self.lock.acquire()
        client = self.clients[ client_id ]
        if client:
            client[ "lock" ].acquire()
        return client # Passes a reference to a client's info
        #self.lock.release()

    def delete(self, client_id):
        client = self.clients[client_id]
        if client:
            client["lock"].acquire()
        del self.clients[client_id]

    def getClientsWatching(self, path):
        watchers = []
        for id,client in self.clients:
            if client.isWatching(path):
                watchers.append(client)
        return watchers

    def notifyClientsWatching(self, path, message):
        watchers = self.getClientsWatching(path)
        while watchers:
            for client in watchers:
                success = client.lock.acquire(timeout=1)
                if success:
                    try:
                        client.send(message)
                    finally:
                        client.lock.release()

    def notifyClient(self, index):