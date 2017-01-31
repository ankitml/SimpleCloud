import threading

class ClientRegistry(threading.Thread):
    def __init__(self):
        self.lock = threading.Lock()
        self.clients = {}
        self.client_id = 0

    def put(self, client):
        client[ "lock" ] = threading.Lock
        self.lock.acquire()
        self.client_id += 1
        self.clients[ self.client_id ] = client
        self.lock.release()

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