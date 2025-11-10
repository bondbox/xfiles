#!/usr/bin/python3
# coding:utf-8

import hashlib
import os
import shutil
import unittest

from xkits_file.scanner import Scanner


def handler(obj: Scanner.Object) -> bool:
    return isinstance(obj, Scanner.Object)


class TestScanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.scanner = Scanner.load(
            paths=[os.path.join("xkits_file")],
            exclude=[os.path.join("xkits_file", "unittest")],
            handler=handler)

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load(self):
        self.assertIsInstance(Scanner.load(paths=[os.path.join("scanloader")], handler=handler), Scanner)  # noqa:E501

    def test_iter(self):
        for object in self.scanner:
            self.assertIsInstance(object, Scanner.Object)
            self.assertIsInstance(object.path, str)
            self.assertIsInstance(object.abspath, str)
            self.assertIsInstance(object.realpath, str)
            self.assertIsInstance(object.uid, int)
            self.assertIsInstance(object.gid, int)
            self.assertIsInstance(object.mode, int)
            self.assertIsInstance(object.size, int)
            self.assertIsInstance(object.ctime, float)
            self.assertIsInstance(object.atime, float)
            self.assertIsInstance(object.mtime, float)
            self.assertIsInstance(object.isdir, bool)
            self.assertIsInstance(object.isfile, bool)
            self.assertIsInstance(object.islink, bool)

            if object.isfile and not object.issym:
                self.assertIsInstance(object.hash(hashlib.md5())[0], str)
                self.assertIsInstance(object.hash(hashlib.sha1())[0], str)
                self.assertIsInstance(object.hash(hashlib.sha256())[0], str)

    def test_dirs(self):
        for object in self.scanner.dirs:
            self.assertTrue(object.isdir)

    def test_files(self):
        for object in self.scanner.files:
            self.assertTrue(object.isfile)
            self.assertTrue(object.isreg)

    def test_links(self):
        for object in self.scanner.links:
            self.assertTrue(object.issym)

    def test_add_dir_object(self):
        object = Scanner.Object(os.path.join("xkits_file", "unittest"))
        self.scanner.add(object)
        self.assertIs(self.scanner[object.path], object)

    def test_add_sym_object(self):
        path = shutil.which("sh")
        if path:
            object = Scanner.Object(path)
            self.scanner.add(object)
            self.assertIs(self.scanner[path], object)


if __name__ == "__main__":
    unittest.main()
