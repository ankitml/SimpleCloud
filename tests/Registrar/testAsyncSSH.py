import asyncio
import asyncssh
import paramiko
import threading
import time

from tests.SSHCommunication.asyncSSH.SSHServer import SSHServer

PORT=3509
SERVER_KEYS = CLIENT_KEYS = ["/home/francisco/.ssh/id_rsa"]
AUTHORIZED_KEYS = ["/home/francisco/.ssh/authorized_keys"]

class Server(threading.Thread):
    def __init__(self):
        super(Server, self).__init__()

    async def create_server(self):
        await asyncssh.create_server(SSHServer, host="localhost", port=PORT, server_host_keys=SERVER_KEYS)
    async def start_server(self):
        await asyncssh.listen(host="localhost", port=PORT, server_host_keys=SERVER_KEYS,
                              authorized_client_keys=AUTHORIZED_KEYS, session_factory=SSHServer)
    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.create_server())
        except (OSError, asyncssh.Error) as exc:
            exit('Error starting server: ' + str(exc))
        loop.run_forever()

server = Server()
server.start()
time.sleep(1)
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.WarningPolicy())
client.connect('localhost', port=3509, pkey=paramiko.RSAKey(CLIENT_KEYS[0]))