# coding:utf-8

import os
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from xkits_file import safefile


class TestSafeKits(unittest.TestCase):

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
        with TemporaryDirectory() as temp:
            with safefile.SafeKits.lock(os.path.join(temp, "test")):
                pass

    def test_backup_and_restore(self):
        with TemporaryDirectory() as temp:
            path = os.path.join(temp, "test")
            self.assertTrue(safefile.SafeKits.create_backup(path, copy=False))
            with open(path, "w") as whdl:
                whdl.write(self.text)
            self.assertTrue(safefile.SafeKits.create_backup(path, copy=True))
            self.assertFalse(safefile.SafeKits.create_backup(path, copy=False))
            self.assertFalse(safefile.SafeKits.create_backup(path, copy=True))
            with open(path, "w") as whdl:
                whdl.write("unittest")
            self.assertTrue(safefile.SafeKits.restore(path))
            self.assertTrue(safefile.SafeKits.restore(path))
            self.assertTrue(safefile.SafeKits.restore(path))
            with open(path, "r") as rhdl:
                self.assertEqual(rhdl.read(), self.text)
            self.assertTrue(safefile.SafeKits.create_backup(path, copy=False))
            self.assertFalse(safefile.SafeKits.create_backup(path, copy=True))
            self.assertFalse(safefile.SafeKits.create_backup(path, copy=False))
            self.assertTrue(safefile.SafeKits.delete_backup(path))
            self.assertTrue(safefile.SafeKits.delete_backup(path))
            self.assertTrue(safefile.SafeKits.delete_backup(path))


class TestBaseFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.file = os.path.join(cls.temp.name, "test.txt")
        cls.text = b"bitag5e3ebfbhnxz270c8y8i3s53ruz1"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_check(self):
        self.assertRaises(FileNotFoundError, safefile.BaseFile,
                          filepath=self.file, readonly=True)
        self.assertIsInstance(safefile.BaseFile(self.file, readonly=False),
                              safefile.BaseFile)

    @mock.patch.object(safefile, "open")
    def test_mock_open(self, mock_open):
        with mock.mock_open(mock_open, read_data=self.text):
            with safefile.BaseFile(self.file, readonly=False) as fhdl:
                self.assertEqual(fhdl.read(), self.text)

        with mock.mock_open(mock_open, read_data=self.text.decode()):
            with safefile.BaseFile(self.file, readonly=False, encoding="utf-8") as fhdl:  # noqa:E501
                self.assertEqual(fhdl.read(), self.text.decode())

    def test_read_write(self):
        def binary(fhdl: safefile.BaseFile):
            return fhdl.binary

        def text(fhdl: safefile.BaseFile):
            return fhdl.text

        bfile = safefile.BaseFile(self.file, readonly=False, truncate=True)
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)
        bfile.open()
        self.assertRaises(TypeError, text, bfile)
        bfile.binary.write(self.text)
        bfile.sync()
        bfile.close()
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)

        bfile = safefile.BaseFile(self.file, readonly=True)
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)
        bfile.open()
        self.assertRaises(TypeError, text, bfile)
        self.assertEqual(bfile.binary.read(), self.text)
        bfile.sync()
        bfile.close()
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)

        bfile = safefile.BaseFile(self.file, readonly=True, encoding="utf-8")
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)
        bfile.open()
        self.assertRaises(TypeError, binary, bfile)
        self.assertEqual(bfile.text.read(), self.text.decode())
        bfile.sync()
        bfile.close()
        self.assertRaises(TypeError, binary, bfile)
        self.assertRaises(TypeError, text, bfile)
        self.assertIsNone(bfile.fhandler)


class TestSafeFile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.file = os.path.join(cls.temp.name, "test.txt")
        cls.text = b"izun4drdy50si2xwu4zvmt90johbgewx"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_backup_and_restore(self):
        sfile = safefile.SafeFile(self.file, readonly=False)
        sfile.open()
        sfile.binary.write(self.text)
        sfile.sync()
        sfile.backup(copy=False)
        self.assertEqual(sfile.binary.read(), b"")
        self.assertRaises(Warning, sfile.backup, copy=True)
        self.assertRaises(Warning, sfile.backup, copy=False)
        self.assertIsNone(sfile.fhandler)
        sfile.open()
        self.assertEqual(sfile.binary.read(), b"")
        sfile.binary.write(b"test")
        sfile.close()

        sfile = safefile.SafeFile(self.file, readonly=True)
        sfile.open()
        self.assertEqual(sfile.binary.read(), b"test")
        sfile.restore()
        sfile.restore()
        self.assertEqual(sfile.binary.read(), self.text)
        sfile.close()

        sfile = safefile.SafeFile(self.file, readonly=False)
        sfile.open()
        sfile.binary.write(b"test")
        sfile.sync()
        sfile.close()

        sfile = safefile.SafeFile(self.file, readonly=True)
        sfile.open()
        self.assertEqual(sfile.binary.read(), self.text + b"test")
        sfile.backup(copy=True)
        self.assertEqual(sfile.binary.read(), b"")
        sfile.binary.seek(0)
        self.assertEqual(sfile.binary.read(), self.text + b"test")
        self.assertRaises(Warning, sfile.backup, copy=False)
        self.assertIsNone(sfile.fhandler)
        self.assertRaises(Warning, sfile.backup, copy=True)
        self.assertIsNone(sfile.fhandler)
        self.assertEqual(sfile.open().read(), self.text + b"test")
        sfile.restore()
        self.assertEqual(sfile.binary.read(), self.text + b"test")
        sfile.restore()
        self.assertEqual(sfile.binary.read(), self.text + b"test")
        sfile.backup(copy=False)
        self.assertIsNone(sfile.fhandler)
        self.assertRaises(FileNotFoundError, sfile.open)
        self.assertRaises(Warning, sfile.backup, copy=True)
        self.assertRaises(Warning, sfile.backup, copy=False)

    def test_restore_failure(self):
        with mock.patch.object(safefile.SafeKits, "restore") as mock_restore:
            mock_restore.return_value = False
            sfile = safefile.SafeFile(self.file, readonly=False)
            self.assertRaises(Warning, sfile.restore)


if __name__ == "__main__":
    unittest.main()
