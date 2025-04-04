# coding:utf-8

import os
from tempfile import TemporaryDirectory
import unittest

from xkits_file.safefile import SafeFile


class TestSafeFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.text = "ZbbwpP4%oSwYxP=t+LkyXXzqL9fE8!"

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_lock(self):
        with SafeFile.lock("test"):
            pass

    def test_backup_and_restore(self):
        with TemporaryDirectory() as thdl:
            path = os.path.join(thdl, "test")
            self.assertTrue(SafeFile.create_backup(path))
            with open(path, "w") as whdl:
                whdl.write(self.text)
            self.assertTrue(SafeFile.create_backup(path, copy=True))
            self.assertTrue(SafeFile.create_backup(path))
            with open(path, "w") as whdl:
                whdl.write("unittest")
            self.assertTrue(SafeFile.restore(path))
            with open(path, "r") as rhdl:
                self.assertEqual(rhdl.read(), self.text)
            self.assertTrue(SafeFile.create_backup(path, copy=False))
            self.assertTrue(SafeFile.delete_backup(path))


if __name__ == "__main__":
    unittest.main()
