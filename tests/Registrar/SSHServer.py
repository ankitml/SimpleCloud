import asyncssh, asyncio, threading

class SSHServer(asyncssh.SSHServer):
    def connection_made(self, connection):
        print('SSH connection received from '+
              connection.get_extra_info('peername')[0])
        self.connection = connection
    def connection_lost(self, exc):
        print("[SSHServer] Lost connection"+(" poorly: "+str(exc) if exc else ""))
    def public_key_auth_supported(self):
        return True
    def begin_auth(self, username):
        print("Authenticating user "+username)
        return True
    def handle_session(stdin, stdout, stderr):
        print("Got a session")
        stdout.write('Welcome to my SSH server, '+
                     stdout.channel.get_extra_info('username')+'\n')
        stdout.channel.exit(0)

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
def handle_session(stdin, stdout, stderr):
    print("Got a session")
    stdout.write('Welcome to my SSH server, ' +
                 stdout.channel.get_extra_info('username') + '\n')
    stdout.channel.exit(0)

async def create_server(host, port, server_keys, authorized_clients):
    await asyncssh.listen(host=host, port=port, server_host_keys=server_keys,
                        authorized_client_keys=authorized_clients,
                        session_factory=handle_session)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(create_server(host="localhost", port="3509",
                                              server_keys="/home/francisco/.ssh/id_rsa",
                                              authorized_clients="/home/francisco/.ssh/authorized_keys"))
    except (OSError, asyncssh.Error) as exc:
        exit('Error starting server: ' + str(exc))
    loop.run_forever()