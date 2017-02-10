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
                file.write(string_common+filename)
        self.tasks = queue.Queue()
        self.observer = Observer()
        handler1 = FileSystemEventHandler(localRoot=local_dir, remoteRoot=remote_dir, tasks=self.tasks)
        self.watch = self.observer.schedule(event_handler=handler1, path=local_dir)
        self.observer.start()

    # Modifying the file should add a new task to the queue
    def testTaskInsertion(self):
        new_string = "This is a whole new line in file "+filename
        with open (local_dir+filename, "w") as local_file:
            local_file.write(new_string)
        while True:
            try:
                task = self.tasks.get(block=True, timeout=1)
            except queue.Empty:
                break
            self.assertEqual(task.src_path,local_dir+filename)
            self.assertEqual(task.dest_path, remote_dir+filename)

    # Tests whether it's possible to add a new Handler to an already scheduled watch
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
            self.assertEqual(task, fake_handle)

    # Scheduling a new watch while another one is running
    # In this test, each write should set off 2 events (open+close) as seen on the next test
    # However watchdog is nice enough to avoid adding similar events to its internal queue
    def testNewScheduling(self):
        self.assertTrue(self.tasks.empty()) # Queue starts off
        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going once")
        self.assertRaises(queue.Empty, self.tasks.get, timeout=1) # No Handler is watching the file yet

        handler2 = FileSystemEventHandler(localRoot=remote_dir, remoteRoot=local_dir, tasks=self.tasks)
        self.observer.schedule(event_handler=handler2, path=remote_dir, recursive=True)

        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going twice")
        l1 = empty_tasks(self.tasks) # Now it should work
        self.assertEqual(len(l1), 1) # Single event
        for task in l1:
            self.assertEqual(task.src_path, remote_dir + filename)
            self.assertEqual(task.dest_path, local_dir + filename)

        with open(local_dir + filename, "w") as local_file:
            local_file.write("Going thrice")
        l2 = empty_tasks(self.tasks)
        self.assertEqual(len(l2), 1)  # Single event
        for task in l2:
            self.assertEqual(task.src_path, local_dir + filename)
            self.assertEqual(task.dest_path, remote_dir + filename)

    def testEventsPerWrite(self):
        local_file = open(local_dir+filename, "w")
        self.assertTrue(len(empty_tasks(self.tasks)) == 1) # Opening sets off an event
        local_file.write("First")
        self.assertTrue(len(empty_tasks(self.tasks)) == 0) # Writing doesn't set off an event
        local_file.write("Second")
        self.assertTrue(len(empty_tasks(self.tasks)) == 0) # Writing doesn't set off an event
        local_file.close()
        self.assertTrue(len(empty_tasks(self.tasks)) == 1) # Closing sets off an event


if __name__ == "__main__":
    unittest.main()

def empty_tasks(tasks):
    l1 = []
    while True:
        try:
            task = tasks.get(timeout=1)
            l1.append(task)
            #print(task.src_path + ' => ' + task.dest_path)
        except queue.Empty:
            break
    return l1