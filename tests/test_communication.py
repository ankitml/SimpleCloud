import unittest
import queue

from server.TaskEmitter import TaskEmitter
from client.TaskReceiver import TaskReceiver

class TestCommunication(unittest.TestCase):
    host = "localhost"
    port = 5017
    emitter_queue = queue.Queue()
    receiver_queue = queue.Queue()
    sync_dirs = []

    def setUp(self):
        global host, port, emitter_queue, receiver_queue, sync_dirs, emitter, receiver
        emitter = TaskEmitter(host, port, emitter_queue)
        receiver = TaskReceiver(host, port, receiver_queue, sync_dirs)

    def test_hello_world(self):
        global emitter, receiver
        emitter_queue.put("Hello, world")
        data = receiver.get()
        self.assertEqual(data, "Hello, world")