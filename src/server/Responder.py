import socket
import pickle
import threading
import queue
import zlib
import itertools
import os
#import pyrsync2 as rsync
import pyzsync as zsync
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent

DEFAULT_BLOCKSIZE = 1024*512

class Responder(threading.Thread):
    def __init__(self, index, channels, incoming, observer, handler):
        threading.Thread.__init__(self)
        self.incoming = (incoming if incoming else queue.Queue())
        self.index = index
        self.channels = channels
        self.observer = observer
        self.stop_event = threading.Event()
        self.handler = handler

    def run(self):
        num_comm = 0
        while not self.stop_event.is_set():
            try:
                action,channel_id,message = self.incoming.get(block=True, timeout=1)
                num_comm += 1
                print("[Responder] Received " + str(message)+" from "+str(channel_id))
                if action == "respond":
                    response = self.handle_message(message, channel_id)
                else:
                    response = message
                if response:
                    self.send(response, channel_id)
                # Case 1 - local filesystem event, notify everyone watching that path
                #if isinstance(item, FileSystemEvent):
                #    self.handle_event(item)
                    #path = item.src_path
                    #print("[Responder] Got event on "+str(item.src_path))
                    #self.notify_all(path, num_comm)
                # Case 2 - received message from client
            except queue.Empty:
                continue
        print("[Responder] Stopping")

    def handle_event(self, event):
        src_path = event.src_path
        self.index.get_watchers(src_path)

    def handle_message(self, message, channel_id):
        action = message["action"]
        #id = message["id"]
        response = {
            "action" : "invalid",
            "message" : "Invalid message ("+action+")"
            #"id": id
        }
        # Case 2.1 - Remote requests watching a directory
        if action == "watch":
            response = self.handle_watch_request(message["paths"], channel_id)
        # Case 2.2 - Remote is now watching the requested directories
        elif action == "watching":
            successful = message["successful"]
            print("[Responder] "+str(channel_id)+" is now watching "+str(successful))
            return
        elif action == "pull":
            # response = self.request_hashes
            print("[Responder] "+str(channel_id)+" wants me to patch "+message["path"])
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
            print("[Responder] My message was invalid: "+message["message"])
            return
        return response

    def request_watch(self, paths, channel_id):
        succeeded = []
        # Schedule local watch with conversion
        for local,remote in paths:
            local = os.path.abspath(local)
            remote = os.path.abspath(remote)
            try:
                watch = self.observer.schedule(self.handler, local)
            except OSError:
                continue
            succeeded.append((id(watch), local, remote))
        self.index.add_watches(channel_id, succeeded)
        request = {
            "action": "watch",
            "id": 1,
            "paths": [watch[2] for watch in succeeded]
        }
        self.send(request, channel_id)

    def handle_watch_request(self, paths, channel_id):
        succeeded = []
        failed = []
        # Schedule watch with no conversion
        for path in paths:
            path = os.path.abspath(path)
            try:
                watch = self.observer.schedule(self.handler, path)
            except OSError:
                failed.append(path)
                continue
            succeeded.append((id(watch), path, path))
        self.index.add_watches(channel_id, succeeded)
        response = {
            "action": "watching",
            "id": id,
            "successful": [watch[1] for watch in succeeded],
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

    def send(self, message, channel_id):
        channel = self.channels[channel_id]
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