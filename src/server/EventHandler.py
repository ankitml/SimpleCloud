from watchdog.events import LoggingEventHandler as LoggingEventHandler_super, FileSystemEventHandler as FileSystemEventHandler_super, FileSystemMovedEvent
import os
import time

class FileSystemEventHandler(FileSystemEventHandler_super):
	def __init__(self, index, messages):
		super(FileSystemEventHandler, self).__init__()
		self.index = index
		self.messages = messages

	def on_any_event(self, event):
		watchers = self.index.get_watchers(event.src_path)
		print("[Handler] Event of type "+event.event_type+
			  " in "+event.src_path+". Sending to "+str(watchers))
		for channel_id,path in watchers:
			self.messages.put((
				"send",
				channel_id,
				{
					"action" : "pull",
					"path" : path
				}
			))

	def get_messages(self):
		return self.messages
	# def on_moved(self, event):
	# 	self.handle_modification(event)
    #
	# def on_modified(self, event):
	# 	if not event.is_directory:
	# 		self.handle_modification(event)
    #
	# def on_created(self, event):
	# 	if event.is_directory:
	# 		self.handle_modification(event)
    #
	# def on_deleted(self, event):
	# 	self.handle_modification(event)
    #
	# def handle_modification(self, event):
	# 	self.client.sendall(event)
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

