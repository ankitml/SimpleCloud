import socket
import ssl
import time
import threading
import pickle

#Server
class TaskEmitter(threading.Thread):
	def __init__(self, host, port, task_queue):
		threading.Thread.__init__(self)
		self.tasks = task_queue

		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.TCPsocket.bind((host, port))
		self.TCPsocket.listen(10)
		self.observe = False
		
		#self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
		#self.SSLsocket.bind((host, port))
		#self.SSLsocket.listen(10)
	
	def __del__(self):
		self.close()
	
	def run(self):
		print("Awaiting client...")
		#self.client_connection,self.client_address = self.SSLsocket.accept()
		self.client_connection,self.client_address = self.TCPsocket.accept()
		print("Connected to " + str(self.client_address))
		self.register_client()

		while not self.observe:
			time.sleep(1)

		while self.observe:
			data = self.tasks.get(block=True)
			self.tasks.task_done()
			print("[Emitter] Received " + str(data) + " from task queue")
			self.client_connection.sendall(pickle.dumps(data))

	def register_client(self):
		sync_dirs = pickle.loads(self.client_connection.recv(1024))
		self.tasks.put(sync_dirs)
		
	def close(self):
		print("Closing server")
		#self.SSLsocket.close()
		self.TCPsocket.close()


# def test():
# 	host = "localhost"
# 	port = 1507
# 	emitter = TaskEmitter(host, port)
# 	emitter.open()
#
# 	while True:
# 		print "Enter your packet:"
# 		packet = raw_input()
# 		emitter.send(packet)
