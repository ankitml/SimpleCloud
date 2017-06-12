import subprocess
import paramiko
import socket
import time
import pickle
import paramiko
import threading
import queue
import select

server_key = paramiko.RSAKey(filename="/home/francisco/.ssh/id_rsa")
authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"

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

class Server(threading.Thread):
    def __init__(self, incoming, outgoing):
        threading.Thread.__init__(self)
        self.incoming = incoming
        self.outgoing = outgoing
        self.keep_running = threading.Event()

    def run(self):
        num_comm = 0
        server_socket = Server.create_socket('localhost', 3509)
        inputs = [ server_socket ]
        self.keep_running.set()
        print("[Server] All set, listening for SSH connections...")

        while self.keep_running.is_set():
            (readables, writables, exceptionals) = select.select(inputs, inputs, inputs, 1)
            print('Inputs: '+str(inputs)+' | Readables: '+str(readables)+' | Writables: '+str(writables))

            # Handle incoming registrations, messages and disconnects
            for readable in readables:
                # 1 - New registration
                if readable is server_socket:
                    client_socket, address = server_socket.accept()
                    channel = Server.negotiate_channel(client_socket)
                    if not channel:
                        continue
                    print("[Server] Now have secure channel with " + str(address))
                    inputs.append(channel)
                else:
                    try:

                        databin = readable.recv(1024 ^ 2)
                        # 2 - Client disconnection
                        if not databin:
                            print("[Server] Disconnection")
                            inputs.remove(readable)
                        # 3 - Client message
                        else:
                            num_comm += 1
                            data = pickle.loads(databin)
                            self.incoming.put({
                                'channel': readable,
                                'data': data,
                                'num' : num_comm
                            })
                            print("Server received: " + str(data))
                    except socket.error:
                        inputs.remove(readable)

            # Handle outgoing messages
            failed = []
            while True:
                try:
                    message = self.outgoing.get(block=False)
                    self.outgoing.task_done()
                    channel = message['channel']
                    data = message['data']
                    databin = pickle.dumps(data)
                    # For some reason, select.select() return writables as an empty list always
                    # So we have to rely on the channel's own check
                    # if channel in writables:
                    if channel.send_ready():
                        try:
                            channel.sendall(databin)
                        except(socket.timeout, socket.error):
                            print('Channel error')
                            failed.append(message)
                        print('Channel could be used')
                    #else:
                    #    print('Channel is not writable')
                    #    failed.append(message)
                except queue.Empty:
                    break
            for message in failed:
                outgoing.put(message)

    @staticmethod
    def negotiate_channel(client_socket):
        handler = paramiko.Transport(client_socket)
        handler.add_server_key(server_key)
        paramiko_server = ParamikoServer(authorized_keys_filename)
        handler.start_server(server=paramiko_server)
        return handler.accept(20)

    @staticmethod
    def create_socket(address, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((address, port))
        server_socket.listen(100)
        return server_socket

class Responder(threading.Thread):
    def __init__(self, incoming, outgoing):
        threading.Thread.__init__(self)
        self.incoming = incoming
        self.outgoing = outgoing
        self.keep_running = threading.Event()

    def run(self):
        self.keep_running.set()
        while self.keep_running.is_set():
            try:
                message = self.incoming.get(block=True, timeout=1)
                channel = message['channel']
                data = message['data']
                num = message['num']
                response = "Acknowledged \"" + data + "\" as message #" + str(num) + " for this session"
                self.outgoing.put({
                    'channel' : channel,
                    'data' : response
                }, block=True)
                print('[Responder] Got: '+data+'   Replied: '+response)
            except queue.Empty:
                continue

if __name__ == '__main__':
    print('Let\'s start...')
    incoming = queue.Queue()
    outgoing = queue.Queue()
    responder = Responder(incoming, outgoing)
    responder.start()
    server = Server(incoming, outgoing)
    server.run()
    while True:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            server.keep_running.clear()
            responder.keep_running.clear()
            server.join()
            responder.join()