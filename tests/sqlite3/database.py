import sqlite3

init_commands = [
	"""CREATE TABLE channels
		(channel_id INTEGER PRIMARY KEY)""",
	"""CREATE TABLE watches
		(channel_id INTEGER REFERENCES channels(channel_id)
			ON DELETE CASCADE ON UPDATE CASCADE,
		local TEXT, remote TEXT)"""
]
insert_commands = [
	"""INSERT INTO channels VALUES (20),(21),(22)""",
	"""INSERT INTO watches VALUES
		(20, "/home/francisco/Pictures", "/mnt/data/Pictures"),
		(20, "/home/francisco/Documents", "/mnt/data/Documents"),
		(21, "/home/maria/Pictures", "/mnt/data/Pictures")
	"""
]
get_commands = [
	"SELECT * FROM watches",
	"SELECT * FROM channels"
]
update_command = "UPDATE channels SET channel_id=40 WHERE channel_id=21"
delete_command = "DELETE FROM channels WHERE channel_id=40"

def print_tables():
	for cmd in get_commands:
		rows = cursor.execute(cmd)
		for row in rows:
			print(row)

db = sqlite3.connect(":memory:")
cursor = db.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
for cmd in init_commands:
	cursor.execute(cmd)
db.commit()

print("Inserting values into the tables")
for cmd in insert_commands:
	cursor.execute(cmd)
db.commit()
print_tables()

print("Updating tables from ID 21 to ID 40")
cursor.execute(update_command)
db.commit()
print_tables()

print("Deleting row with ID 40")
cursor.execute(delete_command)
db.commit()
print_tables()

rows = cursor.execute("SELECT * FROM channels WHERE channel_id=7")
if rows:
	print(str(rows))
	for row in rows:
		print(row)
else:
	print("Invalid queries return empty lists")

try:
	cursor.execute("INSERT INTO channels VALUES (20)")
	print("Duplicate insertion worked")
	try:
		db.commit()
	except sqlite3.IntegrityError:
		print("Duplicate insertion failed only at commit")
except sqlite3.IntegrityError:
	print("Duplicate insertion failed at query")