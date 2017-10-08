import threading
import os
from os import path
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent
from src.common.EventHandler import EventHandler, ConvertingEventHandler

class Index:
	def __init__(self):
		self.database = sqlite3.connect(":memory:", check_same_thread=False)
		#self.cursor = self.database.cursor()
		self.init_db()

	def init_db(self):
		cursor = self.database.cursor()
		commands = [
			"PRAGMA foreign_keys = ON;",
			"""CREATE TABLE channels
				(channel_id INTEGER PRIMARY KEY)""",
			"""CREATE TABLE watches
				(path TEXT PRIMARY KEY, watch_id INTEGER)""",
			"""CREATE TABLE recipients
				(channel_id INTEGER REFERENCES channels(channel_id)
					ON DELETE CASCADE ON UPDATE CASCADE,
				local_path TEXT REFERENCES watches(path), remote_path TEXT)""",
			"""CREATE TABLE instructions
				(path TEXT
				channel_id REFERENCES channels(channel_id),
				instructions BLOB)"""
		]
		for cmd in commands:
			cursor.execute(cmd)
		self.database.commit()

	def add_channel(self, channel_id):
		cursor = self.database.cursor()
		cursor.execute("INSERT INTO channels VALUES (?)", (channel_id,))
		self.database.commit()

	# Unregisters a channel and removes all watches that only exist for that channel
	def remove_channel(self, channel_id):
		cursor = self.database.cursor()
		lone_watches = cursor.execute(
			"""SELECT * FROM recipients WHERE channel_id=? AND local_path IN
				(SELECT local_path FROM recipients GROUP BY local_path HAVING COUNT(*)=1)""",
			(channel_id,))
		cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
		self.database.commit()

	# watches is a list of (watch_id, local, remote)
	def add_watches(self, channel_id, watches):
		cursor = self.database.cursor()
		try:
			for watch_id, local, remote in watches:
				#print(str(channel_id)+" is watching("+str(watch_id)+")"+local+" => "+remote)
				cursor.execute(
					"""INSERT OR IGNORE INTO watches
						VALUES (?,?)""",
					(local, watch_id,))
				cursor.execute(
					"""INSERT OR IGNORE INTO recipients
						VALUES (?,?,?)""",
					(channel_id, local, remote,))
			#self.cursor.execute("INSERT INTO watches VALUES (?,?)", (path, watch_id))
			self.database.commit()
		except sqlite3.IntegrityError:
			print("[Index] Watch "+str(watch_id)+" probably already existed")

	def get_watch_id(self, path):
		cursor = self.database.cursor()
		watch = cursor.execute("SELECT watch_id FROM watches WHERE path = ?", (path))
		return watch.fetchone()

	# Before adding a recipient, there should be a watch already going on
	# and the channel should already be registered
	# I don't see a point for this to exist right now
	# Why would I want to add a watch and not a recipient?
	def add_recipient(self, channel_id, paths):
		try:
			for local,remote in paths:
				print(channel_id + " : " + local + " => " + remote)
				try:
					self.cursor.execute(
						"""INSERT INTO  VALUES (?,?,?)""",
						(channel_id, local, remote)
					)
				except sqlite3.IntegrityError:
					print("[Index] Unable to insert "+str(channel_id)+
						  " : "+local+" => "+remote)
				self.database.commit()
		except sqlite3.IntegrityError:
			print("[Index] Failed to commit transaction")

	# Get a list of (channel_id, remote) where channel_id is
	# interested in 'path' and remote is its remote path
	def get_watchers(self, path):
		cursor = self.database.cursor()
		watchers = cursor.execute(
			"""SELECT channel_id, 
				REPLACE(?, local_path, remote_path)
				FROM recipients
				WHERE ? LIKE local_path||'%'""",
			(path, path,)
		)
		return watchers.fetchall()

	# Get a list of paths that channel_id is watching
	def get_watching(self, channel):
		cursor = self.database.cursor()
		paths = cursor.execute(
			"""SELECT local_path FROM recipients JOIN watches WHERE channel_id = ?""",
			(channel,)
		)
		return paths.fetchall()

	def get_local(self, path):
		pass

	def get_remotes(self, path, channel_id):
		pass

	def add_instructions(self, path, channel_id, instructions_bin):
		cursor = self.database.cursor()
		cursor.execute(
			"""INSERT INTO instructions VALUES (?,?,?)""",
			(path,channel_id,instructions_bin,)
		)
		self.database.commit()

	def get_instructions(self, path, channel_id):
		cursor = self.database.cursor()
		instructions_bin = cursor.execute(
			"""SELECT instructions FROM instructions
				WHERE path=? AND channel_id = ?""",
			(path, channel_id)
		)
		return instructions_bin.fetchone()