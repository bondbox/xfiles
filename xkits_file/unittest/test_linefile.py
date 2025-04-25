# coding:utf-8

from os.path import join
from tempfile import TemporaryDirectory
import unittest

from xkits_file.linefile import LineFile


class TestLineFile(unittest.TestCase):

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

    def test_metadata_parse(self):
        self.assertIsInstance(LineFile.Metadata.parse(b"\x5c\x3a\x6c\x66\x01\x00\x00\x00\xff\xff\xff\x7f"), LineFile.Metadata)  # noqa:E501
        self.assertIsInstance(LineFile.Metadata.parse(b"\x5c\x3a\x6c\x66\xff\xff\xff\x7f\x01\x00\x00\x00"), LineFile.Metadata)  # noqa:E501
        self.assertRaises(ValueError, LineFile.Metadata.parse, b"\x5c\x3a\x6c\x66\xff\xff\xff\xff\xff\xff\xff\x7f")  # noqa:E501
        self.assertRaises(ValueError, LineFile.Metadata.parse, b"\x5c\x3a\x6c\x66\x00\x00\x00\x00\xff\xff\xff\x7f")  # noqa:E501
        self.assertRaises(ValueError, LineFile.Metadata.parse, b"\x5c\x3a\x6c\x66\xff\xff\xff\x7f\xff\xff\xff\xff")  # noqa:E501
        self.assertRaises(ValueError, LineFile.Metadata.parse, b"\x5c\x3a\x6c\x66\xff\xff\xff\x7f\x00\x00\x00\x00")  # noqa:E501

    def test_metadata_new(self):
        self.assertIsInstance((meta := LineFile.Metadata.new(1, 1)), LineFile.Metadata)  # noqa:E501
        self.assertRaises(ValueError, LineFile.Metadata.new, 1, 0)
        self.assertRaises(ValueError, LineFile.Metadata.new, 0, 1)
        self.assertEqual(str(meta), "Metadata(order=1, bytes=1)")

    def test_cursor(self):
        self.assertIsInstance((cursor := LineFile.Cursor(1, 0, b"t")), LineFile.Cursor)  # noqa:E501
        self.assertRaises(ValueError, LineFile.Cursor, 1, -1, b"t")
        self.assertRaises(ValueError, LineFile.Cursor, 1, 1, b"t")
        self.assertRaises(ValueError, LineFile.Cursor, 0, 0, b"t")
        self.assertRaises(ValueError, LineFile.Cursor, 1, 0, b"")
        self.assertEqual(str(cursor), "Cursor(serial=1, offset=0, length=1)")
        self.assertEqual(cursor.serial, 1)
        self.assertEqual(cursor.offset, 0)
        self.assertEqual(cursor.length, 1)

    def test_cursor_prev(self):
        self.assertIsInstance((cursor2 := LineFile.Cursor(2, 25, b"t")), LineFile.Cursor)  # noqa:E501
        self.assertIsInstance((cursor1 := cursor2.prev(b"d")), LineFile.Cursor)
        self.assertRaises(StopIteration, cursor1.prev, b"s")
        self.assertRaises(ValueError, cursor2.prev, b"ut")
        self.assertEqual(cursor2.prev_tail_offset, 13)
        self.assertEqual(cursor1.serial, 1)
        self.assertEqual(cursor1.offset, 0)
        self.assertEqual(cursor1.length, 1)

    def test_cursor_begin(self):
        def prev(cursor: LineFile.Cursor) -> int:
            return cursor.prev_tail_offset

        self.assertIsInstance((cursor := LineFile.Cursor.begin()), LineFile.Cursor)  # noqa:E501
        self.assertEqual(str(cursor), "Cursor(serial=0, offset=0, length=0)")
        self.assertIsInstance((next := cursor.next(b"ut")), LineFile.Cursor)
        self.assertRaises(StopIteration, cursor.prev, 3)
        self.assertRaises(StopIteration, prev, cursor)
        self.assertEqual(cursor.serial, 0)
        self.assertEqual(cursor.offset, 0)
        self.assertEqual(cursor.length, 0)
        self.assertEqual(next.serial, 1)
        self.assertEqual(next.offset, 0)
        self.assertEqual(next.length, 2)
        self.assertFalse(cursor)
        self.assertTrue(next)

    def test_create(self):
        with TemporaryDirectory() as temp:
            self.assertRaises(FileNotFoundError, LineFile, join(temp, "test"))

    def test_dump(self):
        with TemporaryDirectory() as temp:
            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor0 := line.fast_check(), LineFile.Cursor)  # noqa:E501
                self.assertIsInstance(cursor1 := line.dump(b"demo"), LineFile.Cursor)  # noqa:E501
                self.assertEqual(cursor0.serial, 0)
                self.assertEqual(cursor0.offset, 0)
                self.assertEqual(cursor0.length, 0)
                self.assertEqual(cursor1.serial, 1)
                self.assertEqual(cursor1.offset, 0)
                self.assertEqual(cursor1.length, 4)

            with LineFile(join(temp, "test"), readonly=True) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 1)
                self.assertEqual(cursor.offset, 0)
                self.assertEqual(cursor.length, 4)

    def test_dump_error_serial(self):
        with TemporaryDirectory() as temp:
            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.dump(b"demo1"), LineFile.Cursor)  # noqa:E501
                meta = LineFile.Metadata.new(order=(next := cursor.next(b"demo2")).serial, bytes=5)  # noqa:E501
                line.binary.write(bytes(meta))
                line.binary.write(next.content)
                meta.order = 123
                line.binary.write(bytes(meta))
                self.assertEqual(cursor.serial, 1)
                self.assertEqual(cursor.offset, 0)
                self.assertEqual(cursor.length, 5)
                self.assertEqual(next.serial, 2)
                self.assertEqual(next.offset, 29)
                self.assertEqual(next.length, 5)
                self.assertEqual(line.binary.tell(), 58)

            with LineFile(join(temp, "test"), readonly=True) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 1)
                self.assertEqual(cursor.offset, 0)
                self.assertEqual(cursor.length, 5)
                self.assertEqual(line.binary.tell(), 29)
                self.assertEqual(line.binary.seek(0, 2), 58)
                self.assertEqual(line.binary.tell(), 58)

            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 1)
                self.assertEqual(cursor.offset, 0)
                self.assertEqual(cursor.length, 5)
                self.assertEqual(line.binary.tell(), 29)
                self.assertEqual(line.binary.seek(0, 2), 29)
                self.assertEqual(line.binary.tell(), 29)

    def test_check_dirty(self):
        with TemporaryDirectory() as temp:
            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertEqual(line.binary.write(b"1234567890"), 10)
                self.assertEqual(line.binary.tell(), 10)

            with LineFile(join(temp, "test"), readonly=True) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 0)
                self.assertEqual(cursor.offset, 0)
                self.assertEqual(cursor.length, 0)

    def test_check_and_truncate(self):
        with TemporaryDirectory() as temp:
            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor1 := line.dump(b"demo1"), LineFile.Cursor)  # noqa:E501
                self.assertIsInstance(cursor2 := line.dump(b"demo2"), LineFile.Cursor)  # noqa:E501
                self.assertIsInstance(cursor3 := line.dump(b"demo3"), LineFile.Cursor)  # noqa:E501
                self.assertEqual(cursor1.serial, 1)
                self.assertEqual(cursor1.offset, 0)
                self.assertEqual(cursor1.length, 5)
                self.assertEqual(cursor2.serial, 2)
                self.assertEqual(cursor2.offset, 29)
                self.assertEqual(cursor2.length, 5)
                self.assertEqual(cursor3.serial, 3)
                self.assertEqual(cursor3.offset, 58)
                self.assertEqual(cursor3.length, 5)
                self.assertEqual(line.binary.tell(), 87)
                self.assertEqual(line.binary.seek(80, 0), 80)
                self.assertEqual(line.binary.truncate(), 80)

            with LineFile(join(temp, "test"), readonly=True) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 2)
                self.assertEqual(cursor.offset, 29)
                self.assertEqual(cursor.length, 5)
                self.assertEqual(line.binary.tell(), 58)
                self.assertEqual(line.binary.seek(0, 2), 80)
                self.assertEqual(line.binary.tell(), 80)

            with LineFile(join(temp, "test"), readonly=False) as line:
                self.assertIsInstance(line, LineFile)
                self.assertIsInstance(cursor := line.check(), LineFile.Cursor)
                self.assertEqual(cursor.serial, 2)
                self.assertEqual(cursor.offset, 29)
                self.assertEqual(cursor.length, 5)
                self.assertEqual(line.binary.tell(), 58)
                self.assertEqual(line.binary.seek(0, 2), 58)
                self.assertEqual(line.binary.tell(), 58)


if __name__ == "__main__":
    unittest.main()
