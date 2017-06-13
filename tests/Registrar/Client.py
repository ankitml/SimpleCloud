import pickle

import paramiko

class Client:
    def __init__(self, key_filename):
        self.private_key = paramiko.RSAKey(filename=key_filename)
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.WarningPolicy())

    def connect(self, host, port):
        self.client.connect(host, port=port, pkey=self.private_key)
        transport = self.client.get_transport()
        self.channel = transport.open_channel(kind="session")

    def send_get_response(self, action, path):
        message = {
            'action' : action,
            'path' : path
        }
        messagebin = pickle.dumps(message)
        self.channel.sendall(messagebin)
        responsebin = self.channel.recv(1024*1024)
        response = pickle.loads(responsebin)
        return response

if __name__ == "__main__":
    client = Client("localhost", 3509, "/home/francisco/.ssh/fake_key")
    while True:
        action = input("What action would you like to send to the server?\n  > ")
        path = input("On which paths?\n  > ")
        response = client.send_get_response(action, path)
        print("Server replied with:\n  "+response)