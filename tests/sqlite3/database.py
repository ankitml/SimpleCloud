import sqlite3
import unittest

def print_tables(cursor, commands):
	for cmd in commands:
		rows = cursor.execute(cmd)
		for row in rows:
			print(row)

class IndexTests(unittest.TestCase):

	def setUp(self):
		init_commands = [
			"PRAGMA foreign_keys = ON;",
			"""CREATE TABLE channels
				(channel_id INTEGER PRIMARY KEY)""",
			"""CREATE TABLE watches
				(watch_id INTEGER PRIMARY KEY, local TEXT)""",
			"""CREATE TABLE recipients
				(channel_id INTEGER REFERENCES channels(channel_id)
					ON DELETE CASCADE ON UPDATE CASCADE,
				watch_id TEXT REFERENCES watches(watch_id)
					ON DELETE CASCADE ON UPDATE CASCADE,
				remote TEXT)"""
		]
		insert_commands = [
			"""INSERT INTO channels VALUES (20),(21),(22),(23)""",
			"""INSERT INTO watches VALUES
				(1990, "/mnt/data/Pictures"),
				(1992, "/mnt/data/Documents"),
				(1915, "/mnt/data/Videos")
			""",
			"""INSERT INTO recipients VALUES
				(20, 1990, "/home/francisco/Pictures"),
				(20, 1992, "/mnt/data/Documents"),
				(21, 1990, "/home/maria/Pictures"),
				(22, 1915, "/home/antonio/Videos")
			"""
		]
		self.db = sqlite3.connect(":memory:")
		self.cursor = self.db.cursor()
		for cmd in init_commands+insert_commands:
			self.cursor.execute(cmd)
		self.db.commit()
		self.get_commands = [
			"SELECT * FROM watches",
			"SELECT * FROM channels"
		]

	def tearDown(self):
		pass
		#print_tables(self.cursor, self.get_commands)

	def testUpdate(self):
		update_command = "UPDATE channels SET channel_id=40 WHERE channel_id=21"
		self.cursor.execute(update_command)
		self.db.commit()
		get_command = "SELECT * FROM channels WHERE channel_id=40"
		rows = list(self.cursor.execute(get_command))
		self.assertTrue(len(rows) == 1)

	def testDelete(self):
		delete_command = "DELETE FROM channels WHERE channel_id=20"
		self.cursor.execute(delete_command)
		self.db.commit()
		get_command = "SELECT * FROM channels WHERE channel_id=20"
		rows = list(self.cursor.execute(get_command))
		self.assertTrue(len(rows) == 0)

	def testInsertDuplicate(self):
		insert_command = "INSERT INTO channels VALUES (20)"
		self.assertRaises(sqlite3.IntegrityError, self.cursor.execute, insert_command)

	def testGetWatchedByOnlyOne(self):
		cmd = """SELECT * FROM recipients WHERE channel_id=20 AND watch_id IN
			(SELECT watch_id FROM recipients GROUP BY watch_id HAVING COUNT(*)=1)"""
		rows = list(self.cursor.execute(cmd))
		print(rows)
		self.assertTrue(len(rows)==1)

if __name__ == "__main__":
	unittest.main()
