import asyncssh, asyncio, threading, queue, functools

class Server(threading.Thread):
    _clients = []

    def __init__(self, queue):
        super(Server, self).__init__()
        self.queue = queue

    @classmethod
    async def add_client(cls, stdin, stdout, stderr):
        client = cls.Handler(stdin, stdout)
        stdout.write('Welcome!\n')
        Server._clients.append(client)
        #loop = asyncio.get_event_loop()
        print('New client: ' + client.username + '@' + client.address +
              ', currently have ' + str(len(cls._clients)))
        await client.handle_client()
        #task.add_done_callback(Server._clients.remove(client))

    @classmethod
    def remove_client(cls, handler):
        cls._clients.remove(handler)
        print(handler.username + ' has left, currently have '
              + str(len(cls._clients)))

    async def create_server(self, host, port, server_keys, authorized_clients):
        await asyncssh.listen(host=host, port=port, server_host_keys=server_keys,
                              authorized_client_keys=authorized_clients, session_factory=Server.add_client)

    def dispatch(self):
        while True:
            id, message = self.queue.get()
            id = int(id)
            try:
                client = Server._clients[id]
            except IndexError:
                print('No client with that ID')
                continue
            client.send(message)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.create_server(host="localhost", port=3509,
                    server_keys="/home/francisco/.ssh/id_rsa",
                    authorized_clients="/home/francisco/.ssh/authorized_keys"))
        except (OSError, asyncssh.Error) as exc:
            exit('SSH connection failed: ' + str(exc))
        #loop.run_in_executor(executor=None, func=self.dispatch)
        loop.run_forever()

    class Handler:
        def __init__(self, stdin, stdout):
            self._stdin = stdin
            self._stdout = stdout
            sockinfo = stdout.get_extra_info('peername')
            self.username = stdout.get_extra_info('username')
            self.address = str(sockinfo[0])
            #print('New client: ' + self.username + '@' + self.address + ', currently have ' + str(len(Server._clients)))

        async def handle_client(self):
            try:
                async for line in self._stdin:
                    print('[' + self.username + '] ' + line.strip('\n'))
            except asyncssh.BreakReceived:
                pass
            #Server._clients.remove(self)
            print(self.username + ' has left')
            await Server.remove_client(self)

        async def send(self, data):
            print('Sending')
            self._stdout.write(data+'\n')

if __name__ == "__main__":
    queue = queue.Queue()
    server = Server(queue)
    server.start()
    # try:
    #     while True:
    #         client_id = input('Client #> ')
    #         mess = input('Message >')
    #         queue.put((client_id, mess))
    # except KeyboardInterrupt:
    #     print('Bye')