from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super, FileSystemMovedEvent
import os
import time

# For requested watches
class EventHandler(FileSystemEventHandler_super):
	def __init__(self, queue):
		super(EventHandler, self).__init__()
		#self.root = root
		self.queue = queue

	def on_any_event(self, event):
		# Get all channels interested in this event...
		print("[Handler] Received event "+str(event.event_type)+" on "+str(event.src_path))
		self.queue.put(event)

# For independent watches
class ConvertingEventHandler(FileSystemEventHandler_super):
	def __init__(self, queue, channel_id, local_path, remote_path):
		super(ConvertingEventHandler, self).__init__()
		self.queue = queue
		self.channel_id = channel_id
		self.local_path = local_path
		self.remote_path = remote_path

	def on_any_event(self, event):
		src = event.src_path
		src_converted = src.replace(self.local_path, self.remote_path)
		event_converted = type(event)(src_converted)
		event_converted.channel_id = self.channel_id
		print("[Handler] Received event " + str(event_converted.event_type) + " on " + str(src) + " corresponding to " + str(src_converted) + " on destination")
		self.queue.put(event_converted)

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
