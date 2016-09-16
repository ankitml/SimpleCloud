# General tools
import os
import logging
import time

# Multi-threading tools
from queue import Queue

#
import getpass
# import shlex

# Python 3
# import configparser
# Python 2

from src.common import ConfigurationParser
import src.common.Observer as Observer
from .TaskEmitter import TaskEmitter

def get_config():
    global parameters, tasks
    parameters = ConfigurationParser.parse_config()
    print("Parameters: " + str(parameters))

def connect():
    global emitter, tasks
    emitter = TaskEmitter(parameters["host"], parameters["port"], tasks)
    emitter.start()

def watch():
    global observer
    parameters["sync_dirs"] = tasks.get(block=True)
    tasks.task_done()
    emitter.observe = True

    for dir in parameters["sync_dirs"]:
        print("Observe " + dir["remote"] + " and send to " + dir["local"])
    observer = Observer.getObserver(parameters["sync_dirs"], tasks)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping observer")
        observer.stop()
    observer.join()
    print("Here")

global parameters, observer, emitter, tasks
tasks = Queue()

get_config()
connect()
watch()

exit()