from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super
import os
import time

class FileSystemEventHandler(FileSystemEventHandler_super):
	def __init__(self, localRoot, remoteRoot, tasks):
		FileSystemEventHandler_super.__init__(self)
		self.localRoot = os.path.abspath(localRoot)
		self.remoteRoot = os.path.abspath(remoteRoot)
		self.tasks = tasks

		print("[Handler] My root is " + self.localRoot + " and I send to " + remoteRoot)

	def on_modified(self, event):
		print("[Handler] Modified: " + event.src_path)
		source = event.src_path + ("/" if event.is_directory else "")
		destination = self.localPathToRemote(source) + ("/" if event.is_directory else "")
		print("[Handler] Sending to " + destination)
		self.tasks.put({
			"source":source,
			"destination":destination
		}, block=True)
		
	def localPathToRemote(self, localPath):
		relativePath = os.path.relpath(localPath, self.localRoot)
		return os.path.join(self.remoteRoot, relativePath)

class LoggingEventHandler(LoggingEventHandler_super):
	pass
