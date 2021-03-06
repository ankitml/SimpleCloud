import threading
import os

class Index:
    def __init__(self):
        self.lock = threading.Lock()
        # Server
        self.watching = {} # channel-to-paths
        self.watchers = {} # path-to-channels
        # Client
        self.localpaths = {} # remotepath-to-localpath
        self.remote_paths = {}

    def add(self, channel, paths):
        self.lock.acquire()
        if channel in self.watching:
            self.watching[channel].append(paths)
        else:
            self.watching[channel] = paths
        for path in paths:
            if path in self.watchers:
                self.watchers[path].append(channel)
            else:
                self.watchers[path] = [ channel ]
        self.lock.release()

    def remove(self, channel):
        self.lock.acquire()
        paths = self.watching.pop(channel)
        for path in paths:
            self.watchers[path].remove(channel)
            if not self.watchers[path]:
                self.watchers.pop(path)
        self.lock.release()

    def get_watchers(self, path):
        watchers = []
        for watched_path in self.watchers:
            common = os.path.commonpath([watched_path, path])
            if os.path.samefile(common, watched_path):
                watchers.extend(self.watchers[watched_path])
        return watchers
        #return self.watchers[path]

    def get_watching(self, channel):
        return self.watching[channel]

    # Conversion between local paths and remote paths
    # Used by the party that requested a watch for converting
    # the remote event path into a local path
    def add_paths(self, local_root, remote_root, channel_id):
        self.localpaths[ (channel_id, remote_root)] = local_root
        self.remote_paths[ (channel_id, local_root)] = remote_root

    def get_local(self, path):
        for remotepath in self.localpaths:
            common = os.path.commonpath([ remotepath, path ])
            if os.path.samefile(common, remotepath):
                local,_ = self.localpaths[remotepath]
                diff = path.replace(remotepath, "")
                localpath = os.path.join(local, diff)
                print("Local path for "+path+" is "+localpath)
                return localpath

    def get_remotes(self, path, channel_id):
        #return self.remote_paths[(channel_id, local_root)]
        remotes = []
        for key in self.localpaths:
            if key == (channel_id, local_root):
                remote_root = local
                remote_path = path.replace(root, )
                remotes.append()
            common = os.path.commonpath([ remotepath, path ])
            if os.path.samefile(common, remotepath):
                local,_ = self.localpaths[remotepath]
                diff = path.replace(remotepath, "")
                localpath = os.path.join(local, diff)
                print("Local path for "+path+" is "+localpath)
                return localpath
        return remotes