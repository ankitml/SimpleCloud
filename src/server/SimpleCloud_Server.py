# General tools
import os
import logging
import time

# Multi-threading tools
import queue

from src.common import ConfigurationParser
from watchdog.observers import Observer
from src.server.Registrar import Registrar
from src.server.EventHandler import FileSystemEventHandler

def get_config():
    parameters = ConfigurationParser.parse_config()
    print("Parameters: " + str(parameters))
    return parameters

def connect():
    global emitter, tasks
    emitter = TaskEmitter(parameters["host"], parameters["port"], tasks)
    emitter.start()

def watch(sync_dirs):
    global observer
    #parameters["sync_dirs"] = tasks.get(block=True)
    #tasks.task_done()

    for dir in sync_dirs: # parameters["sync_dirs"]:
        print("Observe " + dir["remote"] + " and send to " + dir["local"])
    observer = Observer.getObserver(sync_dirs, tasks) # (parameters["sync_dirs"], tasks)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping observer")
        emitter.join()
        observer.stop()
    observer.join()
    print("Here")

global parameters, observer, emitters, tasks, clients
messages = queue.Queue()

if __name__ == "__main__":
    parameters = get_config()
    observer = Observer()
    handler = FileSystemEventHandler(messages)
    registrar = Registrar(parameters["host"],
                          parameters["port"],
                          parameters["private_key_file"],
                          parameters["authorized_keys_file"],
                          incoming=messages)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping observer")
    registrar.stop()
    observer.stop()
    #connect()
    #watch()