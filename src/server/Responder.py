import socket
import pickle
import threading
import queue
import zlib
import itertools
import os
import pyrsync2 as rsync
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from src.common.EventHandler import IndependentEventHandler, RequestedEventHandler
from src.server.Index import Index

DEFAULT_BLOCKSIZE = 1024*512

class Responder(threading.Thread):
    def __init__(self, incoming=None):
        threading.Thread.__init__(self)
        self.incoming = (incoming if incoming else queue.Queue())
        self.index = Index()
        self.stop_event = threading.Event()
        self.observer = Observer()
        self.independent_handler = IndependentEventHandler(self.incoming)
        self.requested_handler = RequestedEventHandler(self.incoming)

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
        response = {
            "action" : "Invalid message ("+action+")",
            "id": id
        }
        # Case 2.1 - Client wants to watch a directory
        if action == "watch":
            response = self.handle_watch_request(message, channel)
        elif  action == "request_hash":
            response = self.handle_get_hash(message)
        elif action == "sent_hash":
            response = self.handle_get_delta(message)
        # Case 2.2 - Remote wants server to modify its own file
        elif action == "modify":
            response = self.handle_modify(message)
            #hashes = zlib.decompressobj(compressed_hashes)
            self.modify(path, hashes) #No response implemented
            response = {
                "action" : "modified",
                "id" : id,
                "path" : path
            }
        elif action == "watching":
            successful = message["successful"]
            print("[Responder] Server is now watching "+str(successful))
            return
        elif action == "modified":
            path = message["path"]
            print("[Responder] Remote done modifying correspondent to "+str(path))
            return
        elif action == "invalid":
            print("[Responder] Message "+str(id)+" was invalid")
            return
        return response

    def handle_watch_request(self, message, channel):
        paths = message["paths"]
        succeeded = []
        failed = []
        for path in paths:
            watch = self.observer.schedule(self.requested_handler, path)
            succeeded.append(path)
            self.index.add(channel, paths)
        response = {
            "action": "watching",
            "id": id,
            "successful": succeeded,
            "failed": failed
        }
        return response

    def request_watch(self, paths, channel):
        remotes = []
        for local,remote in paths:
            remotes.append(remote)
            self.index.add_paths(local, remote, channel)
            self.observer.schedule(self.independent_handler, local)
        request = {
            "action": "watch",
            "id": 1,
            "paths": remotes
        }
        self.send(request, channel)

    def notify_all(self, path, id):
        channels = self.index.get_watchers(path)
        print(str(channels))
        with open(path, "rb") as file:
            for hash in rsync.blockchecksums(file):
                #print(hash)
                #compressed_hash = zlib.compressobj(hash)
                message = {
                  "id": id,
                  "action": "modify",
                  "path": path,
                  "hashes": [hash]
                }
                #print(str(channels))
                for channel in channels:
                    self.send(message, channel)
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

    def handle_get_hash(self, message):
        path = message["path"]
        try:
            file = open(path, "r+b")
        except FileNotFoundError:
            local_file = open(local_path, "w+b")
        with open(path, "rb") as stream:
            hash = yield from rsync.blockchecksums(stream, blocksize=DEFAULT_BLOCKSIZE)
        response = {
            "action" : "sent_hash",
            "id": message["id"],
            "path" : path,
            "hash" : hash
        }
        return response

    def handle_get_delta(self, message):
        path = message["path"]
        hash = message["hash"]
        with open(path, "rb") as stream:
            delta = rsync.rsyncdelta(stream, hash, blocksize=DEFAULT_BLOCKSIZE, max_buffer=DEFAULT_BLOCKSIZE)
        response = {
            "action": "sent_hash",
            "id": message["id"],
            "path": path,
            "delta": delta
        }
        return response

    def handle_modify(self, message):
        remote_path = message["path"]
        delta = message["delta"]
        local_path = self.index.get_local(remote_path)
        try:
            local_file = open(local_path, "r+b")
        except FileNotFoundError:
            local_file = open(local_path, "w+b")
        delta = rsync.rsyncdelta(local_file, hashes)
        rsync.patchstream(local_file, local_file, delta)
        local_file.close()
        # delta = Responder.peek(delta)
        # if delta:
        #     print("[Responder] Delta is not null, modifying")
        # else:
        #     print("[Responder] Delta is null, files are equal")

    @staticmethod
    def peek(delta):
        try:
            first = next(delta)
            print("[Responder] First element is "+str(first))
            if first == 0:
                return None
        except StopIteration:
            print("[Responder] Delta is null")
            return None
        return itertools.chain([first], delta)

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