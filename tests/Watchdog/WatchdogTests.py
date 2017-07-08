import unittest
import queue
import os
import time
import shutil
from watchdog.observers import Observer
from src.common.EventHandler import EventHandler, ConvertingEventHandler

filename = "t1"
local_dir = os.path.dirname(os.path.realpath(__file__))+"/local/"
remote_dir = os.path.dirname(os.path.realpath(__file__))+"/remote/"
string_common = "This line is in file "

BIG_FILE = "/home/francisco/Firefox_wallpaper.png"
TMP_DIR = "/tmp/SimpleCloud/"
TMP_FILE = os.path.join(TMP_DIR, "file")
BIG_IN = os.path.join(TMP_DIR, "in.png")

class WatchdogTests(unittest.TestCase):

    def setUp(self):
        self.events = queue.Queue()
        self.observer = Observer()
        self.handler = EventHandler(self.events, channel_id=5)
        self.watch = self.observer.schedule(event_handler=self.handler, path=TMP_DIR)
        self.observer.start()

    def testEventChannelID(self):
        with open(TMP_FILE, "w") as local_file:
            local_file.write(string_common)
        event = self.events.get(block=True, timeout=1)
        self.assertEqual(event.channel_id, 5)

    # Modifying the file should add a new task to the queue
    def testTaskInsertion(self):
        new_string = "This is a whole new line in file "+filename
        with open (TMP_FILE, "w") as local_file:
            local_file.write(new_string)
        while True:
            try:
                task = self.events.get(block=True, timeout=1)
            except queue.Empty:
                break
            self.assertEqual(task.src_path,local_dir+filename)
            self.assertEqual(task.dest_path, remote_dir+filename)

    # It should be possible to add a new Handler to an already scheduled watch
    def testHandlerAdding(self):
        fake_handle="I am a fake handler, don't mind me!"
        class FakeHandler(EventHandler):
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
        class HangingHandler(EventHandler):
            def on_any_event(self, event):
                print("Handler hanging...")
                time.sleep(1)
                print("Handler dispatching")
                super().on_any_event(event)

        self.observer.remove_handler_for_watch(self.handler, self.watch)
        slow_handler = HangingHandler(self.events)
        self.observer.add_handler_for_watch(slow_handler, self.watch)
        for i in range(5):
            with open(os.path.join(TMP_DIR, "f"+str(i)), "w") as local_file:
                local_file.write("Write #"+str(i))
            time.sleep(0.1)
        time.sleep(6)
        num = len(empty_tasks(self.events))
        print("[Hanging] "+str(num)+" events")
        self.assertTrue(num >= 5)

    # Scheduling a new watch while another one is running
    # In this test, each write should set off 2 events (open+close) as seen on the next test
    # However watchdog is nice enough to avoid adding similar events to its internal queue
    def testNewScheduling(self):
        self.assertTrue(self.events.empty()) # Queue starts off
        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going once")
        self.assertRaises(queue.Empty, self.events.get, timeout=1) # No Handler is watching the file yet

        handler2 = EventHandler(self.events)
        self.observer.schedule(event_handler=handler2, path=remote_dir, recursive=True)

        with open(remote_dir + filename, "w") as remote_file:
            remote_file.write("Going twice")
        l1 = empty_tasks(self.events) # Now it should work
        self.assertEqual(len(l1), 1) # Single event
        for task in l1:
            self.assertEqual(task.src_path, remote_dir + filename)
            self.assertEqual(task.dest_path, local_dir + filename)

        with open(local_dir + filename, "w") as local_file:
            local_file.write("Going thrice") # Writing to the local file still works
        l2 = empty_tasks(self.events)
        self.assertEqual(len(l2), 1)  # Single event
        for task in l2:
            self.assertEqual(task.src_path, local_dir + filename)
            self.assertEqual(task.dest_path, remote_dir + filename)

    # It should be possible to remove a scheduled watch
    def testWatchRemoval(self):
        handler2 = EventHandler(self.events)
        watch2 = self.observer.schedule(event_handler=handler2, path=remote_dir, recursive=True)
        for client in [ {"path":local_dir+filename, "watch":self.watch},
                      {"path":remote_dir+filename, "watch":watch2} ]:
            with open(client["path"], "w") as file:
                file.write("This will make an event")
            time.sleep(0.5)
            task = self.events.get(timeout=1)
            self.assertEquals(task.src_path, client["path"])

            self.observer.unschedule(client["watch"])
            with open(local_dir+filename, "w") as local_file:
                local_file.write("This won't")
            self.assertRaises(queue.Empty, self.events.get, timeout=1)

    # Each open() and each close() should produce an event
    # They are sometimes squashed into a single event if done
    # Quickly enough (i.e. "with open(file) as f: f.write()")
    def testEventsPerWrite(self):
        local_file = open(local_dir+filename, "w")
        self.assertTrue(len(empty_tasks(self.events)) == 1) # Opening sets off an event
        local_file.write("First")
        self.assertTrue(len(empty_tasks(self.events)) == 0) # Writing doesn't set off an event
        local_file.write("Second")
        self.assertTrue(len(empty_tasks(self.events)) == 0) # Writing doesn't set off an event
        local_file.close()
        self.assertTrue(len(empty_tasks(self.events)) == 1) # Closing sets off an event

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
        num = empty_tasks(self.events)
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