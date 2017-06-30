import unittest
import pyrsync2 as rsync

TEXT = "Mary had a little lamb."

class PyRsyncTests(unittest.TestCase):
    def setUp(self):
        with open("file1", "w") as file1:
            file1.write(TEXT)
        with open("file2", "w") as file2:
            pass

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

if __name__ == "__main__":
    unittest.main()