import socket
import pickle
import threading
import queue

class Responder(threading.Thread):
    def __init__(self, incoming=None):
        threading.Thread.__init__(self)
        self.incoming = (incoming if incoming else queue.Queue())
        self.Index = {}
        self.Watching = {}
        self.keep_running = threading.Event()

    def run(self):
        self.keep_running.set()
        while self.keep_running.is_set():
            try:
                message = self.incoming.get(block=True, timeout=1)
                channel = message['channel']
                data = message['data']
                num = message['num']

                response = self.handle_message(data)
                self.send(response, channel)
                #response = "Acknowledged \"" + data + "\" as message #" + str(num) + " for this session"
                #self.send(response, channel)
            except queue.Empty:
                continue

    @staticmethod
    def handle_message(message):
        action = message['action']
        path = message['path']
        response = "Invalid message ("+action+")"
        if action == 'watch':
            response = '[Responder] Client wants to watch '+str(path)
        return response

    @staticmethod
    def send(message, channel):
        messagebin = pickle.dumps(message)
        if channel.send_ready():
            try:
                channel.sendall(messagebin)
                print('[Responder] Replied: ' + message)
            except(socket.timeout, socket.error):
                print('Channel error')
                # failed.append(message)
                # print('Channel could be used')
        else:
            print('Channel is not writable')