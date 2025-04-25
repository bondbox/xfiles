# coding:utf-8

import unittest

from xkits_fileviewer import main


class TestFileViewer(unittest.TestCase):

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
        self.assertEqual(main(argv=[]), 0)


if __name__ == "__main__":
    unittest.main()
