from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super, FileSystemMovedEvent
import os
import time

class IndependentEventHandler(FileSystemEventHandler_super):
	def __init__(self, queue):
		super(IndependentEventHandler, self).__init__()
		self.queue = queue

	def on_any_event(self, event):
		print("[IndependentHandler] Event "+str(event.event_type)+" on "+str(event.src_path))
		event.watch_type = "independent"
		self.queue.put(event)

class RequestedEventHandler(FileSystemEventHandler_super):
	def __init__(self, queue):
		super(RequestedEventHandler, self).__init__()
		self.queue = queue

	def on_any_event(self, event):
		print("[RequestedHandler] Event " + str(event.event_type) + " on " + str(event.src_path))
		event.watch_type = "requested"
		self.queue.put(event)
"""
	def on_moved(self, event):
		#source = self.localPathToRemote(event.src_path) + ("/" if event.is_directory else "")
		#destination = self.localPathToRemote(event.dest_path) + ("/" if event.is_directory else "")
		#event = FileSystemMovedEvent(source, destination)
		#self.tasks.put(event, block=True)
		self.handle_modification(event)

	def on_modified(self, event):
		if not event.is_directory:
			self.handle_modification(event)

	def on_created(self, event):
		if event.is_directory:
			self.handle_modification(event)

	def on_deleted(self, event):
		self.handle_modification(event)

	def handle_modification(self, event):
		self.client.sendall(event)
		#event.dest_path = self.localPathToRemote(event.src_path) + ("/" if event.is_directory else "")
		#self.tasks.put(event, block=True)
		#print("Found an event on "+event.src_path)

	# def on_any_event(self, event):
		# print("[Handler] Modified: " + event.src_path)
		# source = event.src_path + ("/" if event.is_directory else "")
		#destination = self.localPathToRemote(source) + ("/" if event.is_directory else "")
		# print("[Handler] Sending to " + destination)
		# self.tasks.put(event, block=True)
		# {"source":source,"destination":destination}, block=True)

	#def localPathToRemote(self, localPath):
	#	relative_path = os.path.relpath(localPath, self.localRoot)
	#	return os.path.join(self.remoteRoot, relative_path)
"""
