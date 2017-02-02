from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super, FileSystemMovedEvent
import os
import time

class FileSystemEventHandler(FileSystemEventHandler_super):
	def __init__(self, localRoot, remoteRoot, tasks):
		FileSystemEventHandler_super.__init__(self)
		self.localRoot = os.path.abspath(localRoot)
		self.remoteRoot = os.path.abspath(remoteRoot)
		self.tasks = tasks

		print("[Handler] My root is " + self.localRoot + " and I send to " + remoteRoot)

	def on_moved(self, event):
		source = self.localPathToRemote(event.src_path) + ("/" if event.is_directory else "")
		destination = self.localPathToRemote(event.dest_path) + ("/" if event.is_directory else "")
		event = FileSystemMovedEvent(source, destination)
		self.tasks.put(event, block=True)

	def on_modified(self, event):
		if not event.is_directory:
			self.handle_modification(event)

	def on_created(self, event):
		if event.is_directory:
			self.handle_modification(event)

	def on_deleted(self, event):
		self.handle_modification(event)

	def handle_modification(self, event):
		event.dest_path = self.localPathToRemote(event.src_path) + ("/" if event.is_directory else "")
		self.tasks.put(event, block=True)

	# def on_any_event(self, event):
		# print("[Handler] Modified: " + event.src_path)
		# source = event.src_path + ("/" if event.is_directory else "")
		#destination = self.localPathToRemote(source) + ("/" if event.is_directory else "")
		# print("[Handler] Sending to " + destination)
		# self.tasks.put(event, block=True)
		# {"source":source,"destination":destination}, block=True)

	def localPathToRemote(self, localPath):
		relative_path = os.path.relpath(localPath, self.localRoot)
		return os.path.join(self.remoteRoot, relative_path)

class LoggingEventHandler(LoggingEventHandler_super):
	pass
