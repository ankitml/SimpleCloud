import asyncssh, asyncio, threading, queue

class SSHClientSession(asyncssh.SSHClientSession):
    def data_received(self, data, datatype):
        print(str(data))

    def connection_lost(self, exc):
        if exc:
            print('SSH session error: ' + str(exc))

async def run_client():
    async with asyncssh.connect(host='localhost', port=3509, client_keys="/home/francisco/.ssh/id_rsa",
                                        known_hosts=None) as conn:
        chan, session = await conn.create_session(SSHClientSession)
        while True:
            message = input('> ')
            chan.write(message+'\n')

try:
    loop = asyncio.get_event_loop()
    loop.create_task(run_client())
    loop.run_forever()
except (OSError, asyncssh.Error) as exc:
    exit('SSH connection failed: ' + str(exc))