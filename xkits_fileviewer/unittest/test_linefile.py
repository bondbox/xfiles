# coding:utf-8

from os.path import join
from tempfile import TemporaryDirectory
import unittest

from xkits_command.actuator import ENOTRECOVERABLE

from xkits_fileviewer.linefile import LineFile
from xkits_fileviewer.linefile import main


class TestLine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_main(self):
        self.assertEqual(main(argv=["test"]), ENOTRECOVERABLE)

    def test_reverse(self):
        with TemporaryDirectory() as temp:
            with LineFile(path := join(temp, "test"), readonly=False) as line:
                line.append(b"hello")
                line.append(b"demo1")
                line.append(b"demo2")
                line.append(b"demo3")
                line.append(b"demo4")
                line.append(b"demo5")
            self.assertEqual(main(argv=["--reverse", path]), 0)

    def test_encoding(self):
        with TemporaryDirectory() as temp:
            with LineFile(path := join(temp, "test"), readonly=False) as line:
                line.append(b"hello")
                line.append(b"demo1")
                line.append(b"demo2")
                line.append(b"demo3")
                line.append(b"demo4")
                line.append(b"demo5")
            self.assertEqual(main(argv=["-e", "utf-8", path]), 0)


if __name__ == "__main__":
    unittest.main()
