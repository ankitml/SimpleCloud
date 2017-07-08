import unittest
import os
import time
import shutil
import filecmp
import pyrsync2 as rsync

TEXT = "Mary had a little lamb."
BIG_TEXT = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla quis suscipit mauris. Nam eget imperdiet dui, at varius nulla. Proin mattis interdum elit a malesuada. Mauris malesuada congue sodales. Etiam facilisis egestas enim commodo rutrum. Nullam faucibus porta posuere. Ut feugiat dapibus nulla egestas viverra. Suspendisse consequat est sit amet ligula porttitor auctor. Mauris vehicula sed odio et tincidunt. Suspendisse ut suscipit odio. Fusce aliquet non ipsum eu scelerisque. Sed euismod sit amet leo et volutpat. Mauris risus quam, consectetur a neque in, cursus placerat mauris.

Cras rutrum ipsum ut nibh suscipit hendrerit. Etiam in lacus massa. Quisque imperdiet magna sit amet elit tempus condimentum. Pellentesque sed lacinia lacus. Donec sed libero tortor. Sed dapibus pulvinar sollicitudin. Phasellus vestibulum lectus eu turpis pellentesque, sed interdum dolor eleifend. Vivamus blandit vel est quis interdum. Nam et dictum neque. Pellentesque purus arcu, varius lobortis tempor placerat, pretium vel arcu.

Curabitur sit amet dolor euismod, gravida enim eget, tincidunt neque. Sed in lorem in nisi facilisis efficitur. Donec gravida lacinia mi. Integer scelerisque varius lorem, sit amet malesuada tortor posuere eu. In scelerisque placerat est et interdum. Quisque fringilla, velit porta suscipit consectetur, nunc dui finibus ipsum, in semper orci nisi quis felis. Sed et fringilla lacus. Donec non tincidunt sapien, a ultricies lacus. In hac habitasse platea dictumst. Cras pretium sollicitudin nisi, eu interdum dolor lacinia vitae. In ac malesuada augue. Pellentesque et sapien purus. Quisque accumsan rutrum sem, vitae convallis erat euismod vitae.

Nam pharetra eu ipsum quis tempor. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Proin a nisl nec arcu lacinia varius vel sit amet odio. Curabitur nec fermentum nisl, a volutpat odio. Donec nec felis sed enim luctus pulvinar. Vivamus cursus tortor non lorem tincidunt, eu placerat erat consequat. Morbi varius dui neque, eget interdum nisl efficitur eu. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Ut volutpat eleifend aliquam.

Curabitur tortor turpis, dignissim ac eros non, bibendum imperdiet lorem. Aliquam quis mollis lacus, sit amet posuere risus. Nulla augue elit, vehicula a lobortis ut, blandit vitae enim. Proin nisl neque, bibendum a sodales eget, mattis a tellus. Nulla facilisi. Nam tortor sapien, rutrum eu sem non, tempus venenatis sapien. Quisque vitae augue pretium, bibendum ex a, aliquam nulla. Duis vulputate varius malesuada. Nunc quis congue mi, ac volutpat est. Fusce vel dapibus magna. Aliquam feugiat dolor eget dui eleifend, sit amet facilisis enim convallis. Nunc placerat dolor vel ante fringilla accumsan. Maecenas id nulla ac tortor varius ultrices. Nulla scelerisque mauris quis massa ultrices venenatis. Pellentesque quis faucibus ligula.
"""
# File with a decent size (>1MiB) that should yield plenty of checksums
# Didn't add to git so it doesn't seem like I commited 1 million lines overnight
BIG_FILE = "/home/francisco/Firefox_wallpaper.png"
TMP_DIR = "/tmp/SimpleCloud/"
BIG_IN = os.path.join(TMP_DIR, "in.png")
BIG_OUT = os.path.join(TMP_DIR, "out.png")

class PyRsyncTests(unittest.TestCase):
	def setUp(self):
		with open("file1", "w") as file1:
			file1.write(TEXT)
		with open("file2", "w") as file2:
			pass
		try:
			os.remove(BIG_OUT)
		except FileNotFoundError:
			pass

	@classmethod
	def setUpClass(cls):
		try:
			os.mkdir(TMP_DIR)
		except FileExistsError:
			pass
		try:
			shutil.copy(BIG_FILE, BIG_IN)
		except OSError:
			exit()

	def testCopying(self):
		with open("file1", "r+b") as file1, open("file2", "r+b") as file2:
			hashes2 = rsync.blockchecksums(file2)
			delta = rsync.rsyncdelta(file1, hashes2)
			print(hashes2)
			print(dir(hashes2))
			print(dir(delta))
			rsync.patchstream(file2, file2, delta)
		with open("file2", "r") as file2:
			line = file2.readline()
			self.assertEqual(TEXT, line)
			print(line)

	def testDeltaSameFile(self):
		with open("file1", "r+b") as file1:
			hashes1 = rsync.blockchecksums(file1)
			deltas = rsync.rsyncdelta(file1, hashes1)
			print("Printing deltas for same file:")
			print(deltas)
			for delta in deltas:
				print("d: "+str(delta))

	def testDeltaDifferentFiles(self):
		with open("file1", "r+b") as file1, open("file2", "r+b") as file2:
			hashes2 = rsync.blockchecksums(file2)
			delta = rsync.rsyncdelta(file1, hashes2)
			for i in delta:
				print("i: "+ str(i))
	"""
	Testing a single checksum "list" and a single delta "list
	for a big file
	"""
	def testSingleDeltaForBigFile(self):
		# Create output file
		with open(BIG_OUT, "wb"):
			pass
		start = time.time()
		with open(BIG_OUT, "r+b") as outstream, open(BIG_IN, "rb") as instream:
			hashes = rsync.blockchecksums(outstream)
			deltas = rsync.rsyncdelta(instream, hashes)
			rsync.patchstream(outstream, outstream, deltas)
		finish = time.time()
		elapsed = finish - start
		print("Took " + str(elapsed) + " seconds")
		self.assertTrue(filecmp.cmp(BIG_IN, BIG_OUT, shallow=False))

	"""
	Testing if getting all the checksums, one delta at a time
	for the checksums, and patching each delta individually
	will yield the same file
	"""
	def testMultipleDeltasForBigFile(self):
		# Create output file
		with open(BIG_OUT, "wb"):
			pass
		num_deltas = 0
		start = time.time()
		with open(BIG_OUT, "r+b") as outstream, open(BIG_IN, "rb") as instream:
			hashes = rsync.blockchecksums(outstream)
			deltas = rsync.rsyncdelta(instream, hashes)
			for delta in deltas:
				num_deltas += 1
				#print("delta: "+str(delta))
				rsync.patchstream(outstream, outstream, [delta])
		finish = time.time()
		elapsed = finish - start
		print("Took " + str(elapsed) + " seconds and "+str(num_deltas)+" individual deltas")
		self.assertTrue(filecmp.cmp(BIG_IN, BIG_OUT, shallow=False))

if __name__ == "__main__":
	unittest.main()