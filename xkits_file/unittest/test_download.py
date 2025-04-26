# coding:utf-8

from os import chdir
from os import getcwd
from os import makedirs
from os.path import join
from tempfile import TemporaryDirectory
import unittest

from xkits_file import download


class TestDownloader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.url = "https://example.com/"

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_stat(self):
        with TemporaryDirectory() as temp:
            self.assertIsInstance(download.Downloader(self.url, temp).stat, download.FileStat)  # noqa:E501

    def test_chunk_size(self):
        with TemporaryDirectory() as temp:
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=52428800).chunk_size, 8388608)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=33554432).chunk_size, 8388608)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=16777216).chunk_size, 8388608)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=8388608).chunk_size, 8388608)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=4194304).chunk_size, 4194304)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=1048576).chunk_size, 1048576)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=8192).chunk_size, 8192)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=4096).chunk_size, 4096)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=2048).chunk_size, 4096)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp, chunk_size=1024).chunk_size, 4096)  # noqa:E501
            self.assertEqual(download.Downloader(self.url, temp).chunk_size, 1048576)  # noqa:E501

    def test_prepare(self):
        with TemporaryDirectory() as temp:
            downloader = download.Downloader(self.url, temp)
            makedirs(downloader.path)
            self.assertFalse(downloader.prepare())

    def test_cleanup(self):
        with TemporaryDirectory() as temp:
            downloader = download.Downloader(self.url, temp)
            with open(downloader.temp, "w") as whdl:
                whdl.write("test")
            self.assertTrue(downloader.cleanup())

    def test_complete(self):
        with TemporaryDirectory() as temp:
            self.assertFalse(download.Downloader(self.url, temp).complete())

    def test_start(self):
        with TemporaryDirectory() as temp:
            pwd = getcwd()
            chdir(temp)
            self.assertTrue(download.Downloader(self.url).start())
            self.assertTrue(download.Downloader(self.url, join(temp, "demo")).start())  # noqa:E501
            self.assertRaises(FileExistsError, download.Downloader(self.url, temp).start)  # noqa:E501
            self.assertTrue(download.Downloader(self.url, join(temp, "test", "demo")).start())  # noqa:E501
            self.assertTrue(download.Downloader(self.url, join(temp, "test")).start())  # noqa:E501
            self.assertFalse(download.Downloader("https://test.unkown", temp).start())  # noqa:E501
            chdir(pwd)


if __name__ == "__main__":
    unittest.main()
