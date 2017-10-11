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
                side,channel_id,message = self.incoming.get(block=True, timeout=1)
                num_comm += 1
                print("[Responder] Received " + str(message)+" from "+str(channel_id))
                if side == "respond": # I received this message and should respond
                    response = self.get_response(message, channel_id)
                else: # side == "send" I am supposed to send this message
                    response = message
                if response:
                    self.send(response, channel_id)
            except queue.Empty:
                continue
        print("[Responder] Stopping")

    def get_response(self, message, channel_id):
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
        elif action == "event":
            print("[Responder] " + str(channel_id) + " wants me to patch " + message["path"])
            response = self.handle_event(message, channel_id)
        # Case 2.4 - Remote is requesting blocks according to a list of indexes
        elif action == "request_delta":
            print("[Responder] " + str(channel_id) + " wants blocks for file " + message["path"])
            response = self.handle_request_delta(message, channel_id)
        # Case 2.5 - Remote has sent requested blocks
        elif action == "deliver_blocks":
            response = self.handle_received_blocks(message)
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

    # Handles a message notifying of a remote event with a
    # list of hashes for that file
    # Responds by asking for the delta for that file
    def handle_event(self, message, channel_id):
        pass
        hashes = message["hashes"]
        remote_path = message["path"]
        path = self.index.get_local(remote_path, channel_id)
        with open(path, "rb") as unpatched:
            instructions,request = zsync.zsync_delta(unpatched, hashes)
        # save instructions + request in Index
        self.index.add_instructions(
            path, channel_id, pickle.dumps(instructions))
        return {
            "action" : "request_delta",
            "path" : remote_path,
            "delta" : request
        }

    # Handle a message containing hashes and requesting the
    # delta between them and the hashes for a path
    def handle_request_delta(self, message, channel_id):
        remote_path = message["path"]
        path = self.index.get_local(remote_path, channel_id)
        delta = message["delta"]
        with open(path, "rb") as stream:
            blocks = zsync.get_blocks(stream, delta)
        response = {
            "action": "delta",
            "id": message["id"],
            "path": path,
            "blocks": blocks
        }
        return response

    def handle_received_blocks(self, message, channel_id):
        remote_path = message["path"]
        blocks = message["blocks"]
        path = self.index.get_local(remote_path, channel_id)
        local_path_result = local_path + "_temp"
        try:
            local_file = open(local_path, "r+b")
        except FileNotFoundError:
            local_file = open(local_path, "w+b")
        zsync.easy_patch(local_file, local_path_result, None, blocks)
        local_file.close()

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
    # def handle_received_hashes(self, message):
    #     path = message["path"]
    #     try:
    #         file = open(path, "r+b")
    #     except FileNotFoundError:
    #         local_file = open(local_path, "w+b")
    #     with open(path, "rb") as stream:
    #         hash = yield from zsync.blockchecksums(stream, blocksize=DEFAULT_BLOCKSIZE)
    #     response = {
    #         "action" : "request_delta",
    #         "id": message["id"],
    #         "path" : path,
    #         "hash" : hash
    #     }
    #     return response

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