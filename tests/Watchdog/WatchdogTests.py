import unittest
import queue
import os, time
from watchdog.observers import Observer
from src.common.EventHandler import FileSystemEventHandler

filename = "t1"
local_dir = os.path.dirname(os.path.realpath(__file__))+"/local/"
remote_dir = os.path.dirname(os.path.realpath(__file__))+"/remote/"
string_common = "This line is in file "

class WatchdogTests(unittest.TestCase):

    def setUp(self):
        for filepath in [local_dir+filename, remote_dir+filename]:
            with open(filepath, "w") as file:
                #print("Writing "+string_common+filename+" to "+filename)
                file.write(string_common+filename)
        self.tasks = queue.Queue()
        self.observer = Observer()
        handler1 = FileSystemEventHandler(localRoot=local_dir, remoteRoot=remote_dir, tasks=self.tasks)
        self.watch = self.observer.schedule(event_handler=handler1, path=local_dir)
        self.observer.start()

    def testTaskInsertion(self):
        new_string = "This is a whole new line in file "+filename
        with open (local_dir+filename, "w") as local_file:
            local_file.write(new_string)
        while True:
            try:
                task = self.tasks.get(block=True, timeout=1)
            except queue.Empty:
                break
            self.assertIsNotNone(task)
            self.assertEqual(task.src_path,local_dir+filename)
            self.assertEqual(task.dest_path, remote_dir+filename)

    def testHandlerAdding(self):
        fake_handle="I am a fake handler, don't mind me!"
        class FakeHandler(FileSystemEventHandler):
            def handle_modification(self, event):
                self.tasks.put(fake_handle)
        fake_queue = queue.Queue()
        fake_handler = FakeHandler(localRoot=local_dir, remoteRoot=remote_dir, tasks=fake_queue)
        self.observer.add_handler_for_watch(fake_handler, self.watch)
        new_string = "This is a whole new line in file " + filename
        with open(local_dir + filename, "w") as local_file:
            local_file.write(new_string)
        while True:
            try:
                task = fake_queue.get(block=True, timeout=1)
            except queue.Empty:
                break
            self.assertIsNotNone(task)
            self.assertEqual(task, fake_handle)

if __name__ == "__main__":
    unittest.main()