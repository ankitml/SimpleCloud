from src.server.Registrar import Registrar
from src.server.Responder import Responder
from tests.Registrar.Client import Client
import unittest
import queue

class RegistrarTests(unittest.TestCase):
    def setUp(self):
        key_filename = "/home/francisco/.ssh/id_rsa"
        authorized_keys_filename = "/home/francisco/.ssh/authorized_keys"
        self.host = "localhost"
        self.port = 3509
        self.incoming = queue.Queue()
        self.server = Registrar(self.host, self.port, key_filename, authorized_keys_filename, self.incoming)
        self.server.start()
        self.client = Client(key_filename)

    def tearDown(self):
        self.server.stop()
        self.server.join()

    def testWatchMessage(self):
        self.client.connect(self.host, self.port)
        action = "watch"
        path = ["/home/francisco"]
        response = self.client.send_get_response(action, path)
        expected = "[Responder] Client wants to watch "+str(path)
        self.assertEqual(response, expected)

if __name__ == "__main__":
    unittest.main()