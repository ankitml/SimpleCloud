import asyncio, socket, paramiko
from tests.SSHCommunication.Server import ParamikoServer

class SSHProtocol(asyncio.BaseProtocol):
    key = paramiko.RSAKey(filename="/home/francisco/.ssh/id_rsa")
    authorized = "/home/francisco/.ssh/authorized_keys"

    def connection_made(self, transport):
        self.transport = transport
        print("[Server] Received client connection from " + str(transport.get_extra_info(name='peername')))
        server = paramiko.Transport(transport)
        server.add_server_key(self.key)
        paramiko_server = ParamikoServer()
        # The following negotiation may take a while... should be async
        try:
            server.start_server(server=paramiko_server)
            self.channel = server.accept(20)
        except EOFError:
            pass

    def data_received(self, data):
        print('Received '+str(data)+' from client '+str(self.transport.getpeername()))
        data_enc = self.channel.recv(1024)
        print('And Channel contains '+str(data_enc))
        self.channel.sendall('Badabum')
        # Do something with the data

loop = asyncio.get_event_loop()
server_factory = loop.create_server(SSHProtocol, host='localhost', port=3509)
server = loop.run_until_complete(server_factory)
print('Server running on '+str(server.sockets[0].getsockname()))
try :
    loop.run_forever()
finally:
    loop.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
