import asyncssh, asyncio

# class SSHServerSession(asyncssh.SSHServerSession):
#     def __init__(self):
#         self.chan = None
#     def connection_made(self, chan):
#         print('Creating channel')
#         self.chan = chan
#     def session_started(self):
#         print('Began session')
#         self.chan.write('Welcome!')
#     def data_received(self, data, datatype):
#         print('Received: ' + data)
#     def connection_lost(self, exc):
#         print("Lost session " + (" poorly: " + str(exc) if exc else ""))
# class SSHServer(asyncssh.SSHServer):
#     def public_key_auth_supported(self):
#         return True
#     def session_requested(self):
#         print("Session requested")
#         return SSHServerSession()
    #def connection_made(self):
    #    print('Connection made')

        # stdout.write('Welcome to my SSH server, '+
        #              stdout.channel.get_extra_info('username')+'\n')
        # stdout.channel.exit(0)

# class Server(threading.Thread):
#     def __init__(self, host, port, server_keys, authorized_keys):
#         super(Server, self).__init__()
#         self.host = host
#         self.port = port
#         self.server_keys = server_keys
#         self.authorized_keys = authorized_keys
#
#     async def create_server(self):
#         await asyncssh.create_server(SSHServer, host="localhost", port=self.port,
#                 server_host_keys=self.server_keys, authorized_client_keys=self.authorized_keys)
#
#     def run(self):
#         print("Running")
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             loop.run_until_complete(self.create_server())
#         except (OSError, asyncssh.Error) as exc:
#             exit('Error starting server: ' + str(exc))
#         loop.run_forever()

# async def create_server(host, port, server_keys, authorized_clients):
#     await asyncssh.create_server(SSHServer, host=host,
#                                  port=port, server_host_keys=server_keys,
#                                  authorized_client_keys=authorized_clients)

class Client:
    _clients = []
    def __init__(self, stdin, stdout):
        self._stdin=stdin
        self._stdout=stdout
        Client._clients.append(self)
        sockinfo = stdout.get_extra_info('peername')
        self.username=stdout.get_extra_info('username')
        self.address=str(sockinfo[0])
        print('New client: ' + self.username + '@' + self.address+', currently have '+str(len(Client._clients)))
    @classmethod
    async def add_client(cls, stdin, stdout, stderr):
        client=cls(stdin, stdout)
        stdout.write('Welcome!\n')
        await client.handle_client()
    async def handle_client(self):
        try:
            async for line in self._stdin:
                print('['+self.username+'] '+line.strip('\n'))
        except asyncssh.BreakReceived:
            pass
        Client._clients.remove(self)
        print(self.username + ' has left')

async def create_server(host, port, server_keys, authorized_clients):
    await asyncssh.listen(host=host, port=port, server_host_keys=server_keys,
                        authorized_client_keys=authorized_clients, session_factory=Client.add_client)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(create_server(host="localhost", port="3509",
                                              server_keys="/home/francisco/.ssh/id_rsa",
                                              authorized_clients="/home/francisco/.ssh/authorized_keys"))
    except (OSError, asyncssh.Error) as exc:
        exit('Error starting server: ' + str(exc))
    loop.run_forever()