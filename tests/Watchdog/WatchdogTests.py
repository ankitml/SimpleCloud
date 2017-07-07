import unittest
import queue
import os
import time
import shutil
from watchdog.observers import Observer
from src.common.EventHandler import FileSystemEventHandler

filename = "t1"
local_dir = os.path.dirname(os.path.realpath(__file__))+"/local/"
remote_dir = os.path.dirname(os.path.realpath(__file__))+"/remote/"
string_common = "This line is in file "

BIG_FILE = "/home/francisco/Firefox_wallpaper.png"
TMP_DIR = "/tmp/SimpleCloud/"
BIG_IN = os.path.join(TMP_DIR, "in.png")

class WatchdogTests(unittest.TestCase):

    def setUp(self):
        for filepath in [local_dir+filename, remote_dir+filename]:
            with open(filepath, "w") as file:
                file.write(string_common+filename)
        self.tasks = queue.Queue()
        self.observer = Observer()
        self.handler = FileSystemEventHandler(self.tasks)
        self.watch = self.observer.schedule(event_handler=self.handler, path=local_dir)
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

    # It should be possible to add a new Handler to an already scheduled watch
    def testHandlerAdding(self):
        fake_handle="I am a fake handler, don't mind me!"
        class FakeHandler(FileSystemEventHandler):
            def handle_modification(self, event):
                self.tasks.put(fake_handle)
        fake_queue = queue.Queue()
        fake_handler = FakeHandler(fake_queue)
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

    # A Handler blocking on one event (ex: inserting into a busy queue)
    # should not prevent handling of further events
    def testHandlerHanging(self):
        class HangingHandler(FileSystemEventHandler):
            def handle_modification(self, event):
                print("Handler hanging...")
                time.sleep(3)
                print("Handler dispatching")
                super().handle_modification(event)

        for i in range(5):
            with open(local_dir+filename, "w") as local_file:
                local_file.write("Write #"+str(i))
            time.sleep(0.5)
        #time.sleep(6)
        j=0
        while True:
            try:
                task = self.tasks.get(timeout=4)
                self.assertEquals(task.src_path, local_dir+filename)
                j += 1
            except queue.Empty: break

        self.assertEquals(j, 5)

    # Scheduling a new watch while another one is running
    # In this test, each write should set off 2 events (open+close) as seen on the next test
    # However watchdog is nice enough to avoid adding similar events to its internal queue
    def testNewScheduling(self):
        self.assertTrue(self.tasks.empty()) # Queue starts off
        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going once")
        self.assertRaises(queue.Empty, self.tasks.get, timeout=1) # No Handler is watching the file yet

        handler2 = FileSystemEventHandler(self.tasks)
        self.observer.schedule(event_handler=handler2, path=remote_dir, recursive=True)

        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going twice")
        l1 = empty_tasks(self.tasks) # Now it should work
        self.assertEqual(len(l1), 1) # Single event
        for task in l1:
            self.assertEqual(task.src_path, remote_dir + filename)
            self.assertEqual(task.dest_path, local_dir + filename)

        with open(local_dir + filename, "w") as local_file:
            local_file.write("Going thrice") # Writing to the local file still works
        l2 = empty_tasks(self.tasks)
        self.assertEqual(len(l2), 1)  # Single event
        for task in l2:
            self.assertEqual(task.src_path, local_dir + filename)
            self.assertEqual(task.dest_path, remote_dir + filename)

    # It should be possible to remove a scheduled watch
    def testWatchRemoval(self):
        handler2 = FileSystemEventHandler(self.tasks)
        watch2 = self.observer.schedule(event_handler=handler2, path=remote_dir, recursive=True)
        for client in [ {"path":local_dir+filename, "watch":self.watch},
                      {"path":remote_dir+filename, "watch":watch2} ]:
            with open(client["path"], "w") as file:
                file.write("This will make an event")
            time.sleep(0.5)
            task = self.tasks.get(timeout=1)
            self.assertEquals(task.src_path, client["path"])

            self.observer.unschedule(client["watch"])
            with open(local_dir+filename, "w") as local_file:
                local_file.write("This won't")
            self.assertRaises(queue.Empty, self.tasks.get, timeout=1)

    # Each open() and each close() should produce an event
    # They are sometimes squashed into a single event if done
    # Quickly enough (i.e. "with open(file) as f: f.write()")
    def testEventsPerWrite(self):
        local_file = open(local_dir+filename, "w")
        self.assertTrue(len(empty_tasks(self.tasks)) == 1) # Opening sets off an event
        local_file.write("First")
        self.assertTrue(len(empty_tasks(self.tasks)) == 0) # Writing doesn't set off an event
        local_file.write("Second")
        self.assertTrue(len(empty_tasks(self.tasks)) == 0) # Writing doesn't set off an event
        local_file.close()
        self.assertTrue(len(empty_tasks(self.tasks)) == 1) # Closing sets off an event

    def testEventsForBigFileCopy(self):
        self.observer.schedule(self.handler, TMP_DIR, recursive=True)
        try:
            os.mkdir(TMP_DIR)
        except FileExistsError:
            pass
        try:
            shutil.copy(BIG_FILE, BIG_IN)
        except OSError:
            self.fail()
        num = empty_tasks(self.tasks)
        print("Used "+str(len(num))+" events")

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