import socket
import pickle
import threading
import queue
import zlib
import itertools
import os
import pyrsync2 as rsync
import pyzsync as zsync
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from src.common.EventHandler import EventHandler, ConvertingEventHandler

DEFAULT_BLOCKSIZE = 1024*512

class Responder(threading.Thread):
    def __init__(self, index, incoming=None):
        threading.Thread.__init__(self)
        self.incoming = (incoming if incoming else queue.Queue())
        self.index = index
        self.stop_event = threading.Event()
        self.observer = Observer()
        self.channels = {}

    def run(self):
        num_comm = 0
        self.observer.start()
        while not self.stop_event.is_set():
            try:
                item = self.incoming.get(block=True, timeout=1)
                num_comm += 1
                # Case 1 - local filesystem event, notify everyone watching that path
                if isinstance(item, FileSystemEvent):
                    self.handle_event(item)
                    #path = item.src_path
                    #print("[Responder] Got event on "+str(item.src_path))
                    #self.notify_all(path, num_comm)
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

    def handle_event(self, event):
        src_path = event.src_path
        channel = self.channels[event.channel_id]
        if event.convert_src:
            src_paths = Index.get_remotes()

    def handle_message(self, message, channel):
        action = message["action"]
        id = message["id"]
        response = {
            "action" : "Invalid message ("+action+")",
            "id": id
        }
        # Case 2.1 - Remote requests watching a directory
        if action == "watch":
            response = self.handle_watch_request(message, channel)
        # Case 2.2 - Remote is now watching the requested directory
        elif action == "watching":
            successful = message["successful"]
            print("[Responder] Server is now watching "+str(successful))
            return
        # Case 2.3 - Remote sent a list of hashes to compare to its local file
        elif  action == "deliver_hashes":
            response = self.handle_received_hashes(message)
        # Case 2.4 - Remote is requesting blocks according to a list of indexes
        elif action == "request_blocks":
            response = self.handle_request_blocks(message)
        # Case 2.5 - Remote has sent requested blocks
        elif action == "deliver_blocks":
            responde = self.handle_received_blocks(message)
        # Case 2.6 - Remote has finished modifying its file as requested
        elif action == "modified":
            path = message["path"]
            print("[Responder] Remote done modifying correspondent to "+str(path))
            return
        # A message sent by local was invalid
        elif action == "invalid":
            print("[Responder] Message "+str(id)+" was invalid")
            return
        return response

    def request_watch(self, paths, channel):
        remotes = []
        # Schedule local watch with conversion
        for local,remote in paths:
            remotes.append(remote)
            self.index.add_paths(local, remote, channel)
            channel_id = self.get_channel_id(channel)
            handler = ConvertingEventHandler(self.incoming, channel_id, local, remote)
            watch = self.observer.schedule(handler, local)
        request = {
            "action": "watch",
            "id": 1,
            "paths": remotes
        }
        self.send(request, channel)

    def handle_watch_request(self, message, channel):
        paths = message["paths"]
        succeeded = []
        failed = []
        # Schedule watch with no conversion
        channel_id = self.get_channel_id(channel)
        for path in paths:
            handler = EventHandler(self.incoming)
            watch = self.observer.schedule(handler, path)
            succeeded.append(path)
            self.index.add(channel, paths)
        response = {
            "action": "watching",
            "id": id,
            "successful": succeeded,
            "failed": failed
        }
        return response

    # Handle a message requesting the hashes for a path
    def handle_received_hashes(self, message):
        path = message["path"]
        try:
            file = open(path, "r+b")
        except FileNotFoundError:
            local_file = open(local_path, "w+b")
        with open(path, "rb") as stream:
            hash = yield from rsync.blockchecksums(stream, blocksize=DEFAULT_BLOCKSIZE)
        response = {
            "action" : "request_delta",
            "id": message["id"],
            "path" : path,
            "hash" : hash
        }
        return response

    # Handle a message containing hashes and requesting the delta between them
    # and the hashes for a path
    def handle_request_blocks(self, message):
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

    def handle_received_blocks(self, message):
        remote_path = message["path"]
        blocks = message["blocks"]
        local_path = self.index.get_local(remote_path)
        local_path_result = local_path+"_temp"
        try:
            local_file = open(local_path, "r+b")
        except FileNotFoundError:
            local_file = open(local_path, "w+b")
        zsync.easy_patch(local_file, local_path_result, None, blocks)
        local_file.close()
        # delta = Responder.peek(delta)
        # if delta:
        #     print("[Responder] Delta is not null, modifying")
        # else:
        #     print("[Responder] Delta is null, files are equal")

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
    def get_channel_id(channel):
        return id(channel)

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