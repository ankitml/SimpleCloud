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
        self.observer.start()
        while not self.stop_event.is_set():
            try:
                item = self.incoming.get(block=True, timeout=1)
                num_comm += 1
                # Case 1 - local filesystem event, notify everyone watching
                if isinstance(item, FileSystemEvent):
                    path = item.src_path
                    print("[Responder] Got event on "+str(item.src_path))
                    self.notify_all(path, num_comm)
                # Case 2 - received message from client
                else:
                    channel = item["channel"]
                    message = item["message"]
                    print("[Responder] Received "+str(message))
                    response = self.handle_message(message, channel)
                    if response:
                        self.send(response, channel)
            except queue.Empty:
                continue
        print("[Responder] Stopping")

    def handle_message(self, message, channel):
        action = message["action"]
        id = message["id"]
        response = "Invalid message ("+action+")"
        # Case 2.1 - Client wants to watch a directory
        if action == "watch":
            paths = message["path"]
            succeeded,failed = self.watch(paths, channel)
            response = {
                "action" : "watching",
                "id" : id,
                "successful" : succeeded,
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
        elif action == "watching":
            successful = message["successful"]
            print("[Responder] Server is now watching "+str(successful))
            return
        return response

    def watch(self, paths, channel):
        succeeded = []
        failed = []
        for path in paths:
            watch = self.observer.schedule(self.handler, path)
            succeeded.append(path)
            if "path" in self.Index:
                self.Index["path"].append(channel)
            else:
                self.Index["path"] = [channel]
        return (succeeded,failed)

    def notify_all(self, path, id):
        with open(path, "rb") as file:
            for hash in rsync.blockchecksums(file):
                print(hash)
                #compressed_hash = zlib.compressobj(hash)
                response = {
                  "id": id,
                  "action": "change",
                  "path": path,
                  "hashes": hash
                }
                channels = self.Index[path]
                for channel in channels:
                    self.send(response, channel)
                #hashes = rsync.blockchecksums(file)
        #compressed_hashes = zlib.compressobj(hashes)
        #response = {
        #    "id": id,
        #    "action": "change",
        #    "path": path,
        #    "hashes": compressed_hashes
        #}
        #channels = self.Index[path]
        #for channel in channels:
        #    self.send(response, channel)

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
                print('[Responder] Replied: ' + str(message))
            except(socket.timeout, socket.error):
                print('Channel error')
                # failed.append(message)
                # print('Channel could be used')
        else:
            print('Channel is not writable')

    def stop(self):
        self.stop_event.set()
        self.observer.stop()