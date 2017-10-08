import threading
import os
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from src.common.EventHandler import EventHandler, ConvertingEventHandler

class Index:
	def __init__(self):
		self.database = sqlite3.connect(":memory:")
		self.cursor = self.database.cursor()
		self.init_db()

	def init_db(self):
		commands = [
			"PRAGMA foreign_keys = ON;",
			"""CREATE TABLE channels
				(channel_id INTEGER PRIMARY KEY)""",
			"""CREATE TABLE watches
				(path TEXT PRIMARY KEY, watch_id INTEGER)""",
			"""CREATE TABLE recipients
				(channel_id INTEGER REFERENCES channels(channel_id)
					ON DELETE CASCADE ON UPDATE CASCADE,
				local_path TEXT REFERENCES watches(path), remote_path TEXT)"""
		]
		for cmd in commands:
			self.cursor.execute(cmd)
		self.database.commit()

	def add_channel(self, channel_id):
		self.cursor.execute("INSERT INTO channels VALUES (?)", (channel_id,))
		self.database.commit()

	# Unregisters a channel and removes all watches that only exist for that channel
	def remove_channel(self, channel_id):
		lone_watches = self.cursor.execute(
			"""SELECT * FROM recipients WHERE channel_id=? AND watch_id IN
					(SELECT watch_id FROM recipients GROUP BY watch_id HAVING COUNT(*)=1)""",
			(channel_id,))
		self.cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
		self.database.commit()


	def add_watch(self, path, watch_id):
		try:
			self.cursor.execute("INSERT INTO watches VALUES (?,?)", (path, watch_id))
			self.database.commit()
		except sqlite3.IntegrityError:
			print("[Index] Watch "+str(watch_id)+" probably already existed")

	def get_watch_id(self, path):
		watch = self.cursor.execute("SELECT watch_id FROM watches WHERE path = ?", (path))
		return watch.fetchone()

	# Before adding a recipient, there should be a watch already going on
	# and the channel should already be registered
	def add_recipient(self, channel_id, paths):
		try:
			for local,remote in paths:
				print(channel_id + " : " + local + " => " + remote)
				try:
					self.cursor.execute(
						"INSERT INTO  VALUES (?,?,?)",
						(channel_id, local, remote)
					)
				except sqlite3.IntegrityError:
					print("[Index] Unable to insert "+str(channel_id)+
						  " : "+local+" => "+remote)
				self.database.commit()
		except sqlite3.IntegrityError:
			print("[Index] Failed to commit transaction")

	def get_watchers(self, path):
		watchers = self.cursor.execute(
			"""SELECT channel_id FROM recipients WHERE ? LIKE local_path||'%'""",
			(path,)
		)
		return watchers.fetchall()

	def get_watching(self, channel):
		self.cursor.execute(
			"""SELECT local_path FROM recipients JOIN watches WHERE channel_id = ?""",
			(channel,)
		)

	def get_local(self, path):
		pass

	def get_remotes(self, path, channel_id):
		pass