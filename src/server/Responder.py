import socket
import pickle
import threading
import queue
import zlib
import pyrsync2 as rsync
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from src.common.EventHandler import FileSystemEventHandler

class Responder(threading.Thread):
    def __init__(self, incoming=None):
        threading.Thread.__init__(self)
        self.incoming = (incoming if incoming else queue.Queue())
        self.Index = {}
        self.Watching = {}
        self.stop_event = threading.Event()
        self.observer = Observer()
        self.handler = FileSystemEventHandler(self.incoming)

    def run(self):
        num_comm = 0
        while not self.stop_event.is_set():
            try:
                item = self.incoming.get(block=True, timeout=1)
                num_comm += 1
                # Case 1 - local filesystem event, notify everyone watching
                if item is FileSystemEvent:
                    path = item.src_path
                    self.notify_all(path, num_comm)
                # Case 2 - received message from client
                else:
                    channel = item['channel']
                    message = item['data']
                    response = self.handle_message(message)
                    self.send(response, channel)
            except queue.Empty:
                continue
        print("[Responder] Stopping")

    def handle_message(self, message):
        action = message["action"]
        id = message["id"]
        response = "Invalid message ("+action+")"
        # Case 2.1 - Client wants to watch a directory
        if action == "watch":
            paths = message["paths"]
            succeeded,failed = self.watch(paths)
            response = {
                "action" : "watching",
                "id" : id,
                "succeeded" : succeeded,
                "failed" : failed
            }
        # Case 2.2 - Client wants server to modify its own file
        elif action == "modify":
            path = message["path"]
            compressed_hashes = message["hashes"]
            hashes = zlib.decompressobj(compressed_hashes)
            result = Responder.modify(path, hashes) #No response implemented
            response = {
                "action" : "modified",
                "id" : id,
                "path" : path
            }
        return response

    def watch(self, paths):
        succeeded = []
        failed = []
        for path in paths:
            watch = self.observer.schedule(self.handler, path)
            succeeded.append(path)
        return (succeeded,failed)

    def notify_all(self, path, id):
        with open(path, "rb") as file:
            hashes = rsync.blockchecksums(file)
        compressed_hashes = zlib.compressobj(hashes)
        response = {
            "id": id,
            "action": "change",
            "path": path,
            "hashes": compressed_hashes
        }
        channels = self.Index[path]
        for channel in channels:
            self.send(response, channel)

    @staticmethod
    def modify(path, hashes):
        with open(path, "r+") as local_file:
            delta = rsync.rsyncdelta(local_file, hashes)
            rsync.patchstream(local_file, local_file, delta)

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

    def stop(self):
        self.stop_event.set()
        self.observer.stop()