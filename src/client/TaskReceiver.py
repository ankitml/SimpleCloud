import socket
import ssl
import threading

#Client
class TaskReceiver(threading.Thread):
	def __init__(self, host, port, task_queue):
		threading.Thread.__init__(self)
		self.daemon = True

		self.host = host
		self.port = port
		self.tasks = task_queue
		print type(self.host)
		print type(self.port)
		
		self.TCPsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.TCPsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
		#self.SSLsocket = ssl.wrap_socket(self.TCPsocket, ssl_version=ssl.PROTOCOL_TLSv1)#, ciphers="ADH-AES256-SHA")
	
	def __del__(self):
		self.close()
		
	def run(self):
		#self.SSLsocket.connect((self.host, self.port))
		self.TCPsocket.connect((self.host, self.port))
		print "[Receiver] Connected to "+str(self.host)+":"+str(self.port)
		
		while True:
			data = self.TCPsocket.recv(1024)
			if not data: break
			print "[Receiver] Inserting "+data+" into task queue"
			self.tasks.put(data, block=True)
			#print data

		
	def close(self):
		print "Closing client"
		#self.SSLsocket.close()
		self.TCPsocket.close()

def test():
	import Queue
	host = "localhost"
	port = 1507
	
	receiver = TaskReceiver(host, port, Queue.Queue())
	print "Created receiver"
	receiver.run()

#test()
