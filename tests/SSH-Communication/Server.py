import subprocess
import paramiko
import threading
import socket
import time
import pickle

server_key = paramiko.RSAKey(filename="/home/francisco/.ssh/id_rsa")
authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"

class ParamikoServer(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_publickey(self, username, key):
        print('[Server] Auth attempt with key: ' + str(key.get_base64()))

        authorized_keys = open(authorized_keys_filename, "r")
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

class Server(threading.Thread):
    def run(self):
        while True:
            server_event = threading.Event()
            num_comm = 0

            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', 3509))
            server_socket.listen(100)

            print("[Server] All set, listening for SSH connections...")
            client_socket, address = server_socket.accept()

            print("[Server] Received client connection from "+str(address))
            server = paramiko.Transport(client_socket)
            server.add_server_key(server_key)

            paramiko_server = ParamikoServer()
            server.start_server(server=paramiko_server, event=server_event)
            channel = server.accept(20)
            if not channel:
                continue
            print("[Server] Now have secure channel")
            while True:
                try:
                    datab = channel.recv(1024^2)
                    if not datab:
                        print("[Server] Socket closed")
                        break
                    num_comm += 1
                    data = pickle.loads(datab)
                    print("Server received " + str(data))
                    if not channel:
                        break
                    response = pickle.dumps("Acknowledged \"" + data + "\" as message #" + str(num_comm) +" for this session")
                    channel.send(response)
                except (socket.error, EOFError) as err:
                    break
            server.close()

def start():
    server = Server()
    server.start()
    return server

if __name__ == "__main__":
    start()