from src.server.Index import Index
import unittest

channels = range(20, 24)
# A loose watch, not connected to a channel
watches = [ (23, "/mnt/data/Music") ]
# Watches connected to channels
recipients = [
	(20, [
		(1990, "/mnt/data/Pictures", "/home/francisco/Pictures"),
	  	(1992, "/mnt/data/Documents", "/home/francisco/Documents"),
		]),
	(21, [
		(1990, "/mnt/data/Pictures", "/home/maria/Pictures"),
		]),
	(22, [
		(1915, "/mnt/data/Videos", "/home/antonio/Videos"),
		])
]


class IndexTests(unittest.TestCase):
	def setUp(self):
		self.index = Index()
		for i in channels:
			self.index.add_channel(i)
		#for i,j in watches:
		#	index.add_loose_watches(i,j)
		for i,j in recipients:
			self.index.add_watches(i,j)

	def testWatching(self):
		for channel_id,watches in recipients:
			watching = self.index.get_watching(channel_id)
			expected = [local for _,local,_ in watches]
			# print("Got "+str(watching)+", expected "+str(expected))
			self.assertEqual(watching, expected)
		watching = self.index.get_watching(57)
		self.assertEqual(len(watching), 0)

	def testWatchers(self):
		path = "/mnt/data/Pictures/férias_escócia.jpg"
		watchers = self.index.get_watchers(path)
		self.assertEqual(len(watchers), 2)
		for channel_id,new_path in watchers:
			self.assertTrue(channel_id==20 and new_path=="/home/francisco/Pictures/férias_escócia.jpg"
							or channel_id==21 and new_path=="/home/maria/Pictures/férias_escócia.jpg")
		path = "/var"
		watchers = self.index.get_watchers(path)
		self.assertEqual(len(watchers), 0)

if __name__ == "__main__":
	unittest.main()