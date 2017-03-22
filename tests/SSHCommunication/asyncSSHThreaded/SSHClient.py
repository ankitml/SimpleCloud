import asyncssh, asyncio, threading, queue

class Client(threading.Thread):
    class SSHClientSession(asyncssh.SSHClientSession):
        def data_received(self, data, datatype):
            print(str(data).strip('\n'))

        def connection_lost(self, exc):
            if exc:
                print('SSH session error: ' + str(exc))

    def __init__(self, queue):
        super(Client, self).__init__()
        self.queue = queue
        self.chan = None

    def dispatch(self):
        message = self.queue.get()
        self.chan.write(message+'\n')

    async def run_client(self, loop):
        async with asyncssh.connect(host='localhost', port=3509, client_keys="/home/francisco/.ssh/id_rsa",
                                            known_hosts=None) as conn:
            self.chan, session = await conn.create_session(self.SSHClientSession)
            #i=0
            while True:
                await loop.run_in_executor(executor=None, func=self.dispatch)

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.create_task(self.run_client(loop))
            loop.run_forever()
        except (OSError, asyncssh.Error) as exc:
            exit('SSH connection failed: ' + str(exc))

if __name__ == "__main__":
    queue = queue.Queue()
    client = Client(queue)
    client.start()
    try:
        while True:
            mess = input('> ')
            queue.put(mess)
    except KeyboardInterrupt:
        print('Bye')