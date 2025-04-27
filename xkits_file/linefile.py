# coding:utf-8

from ctypes import Structure
from ctypes import addressof  # noqa:H306
from ctypes import c_uint8
from ctypes import c_uint32  # noqa:H306
from ctypes import memmove
from typing import Any
from typing import BinaryIO
from typing import Generator
from typing import Iterator

from xkits_file.safefile import BaseFile


class LineFile(BaseFile):

    class Metadata(Structure):
        """The metadata of a line is stored at the front and back of the data

        Attributes:
            magic(4bytes): magic number (0x5c, 0x3a, 0x6c, 0x66)
            order(uint32): serial number, start from 1
            bytes(uint32): the length of data in the line
        """
        SINGLE: int = 12
        DOUBLE: int = SINGLE * 2
        MAGIC = b"\x5c\x3a\x6c\x66"

        _fields_ = [
            ("magic", c_uint8 * 4),
            ("order", c_uint32),
            ("bytes", c_uint32),
        ]

        def __str__(self):
            return f"{__class__.__name__}(order={self.order}, bytes={self.bytes})"  # noqa:E501

        def __eq__(self, other) -> bool:
            return self.order == other.order and self.bytes == other.bytes\
                if isinstance(other, self.__class__) else False

        def check_magic(self) -> bool:
            return bytes(self.magic) == self.MAGIC

        @classmethod
        def check_order(cls, order: int) -> bool:
            return 0 < order <= 0x7fffffff

        @classmethod
        def check_bytes(cls, bytes: int) -> bool:  # pylint: disable=W0622
            return 0 < bytes <= 0x7fffffff

        @classmethod
        def parse(cls, datas: bytes):
            if len(datas) < cls.SINGLE:
                raise ValueError(f"Invalid datas: {datas}")

            instance = cls()
            memmove(addressof(instance), datas, cls.SINGLE)
            if not instance.check_magic():
                raise ValueError(f"Invalid magic: {instance.magic}")
            if not instance.check_order(instance.order):
                raise ValueError(f"Invalid order: {instance.order}")
            if not instance.check_bytes(instance.bytes):
                raise ValueError(f"Invalid bytes: {instance.bytes}")
            return instance

        @classmethod
        def new(cls, order: int, bytes: int):  # pylint: disable=W0622
            if not cls.check_order(order):
                raise ValueError(f"Invalid serial: {order}")

            if not cls.check_bytes(bytes):
                raise ValueError(f"Invalid length: {bytes}")

            instance = cls()
            instance.magic = (c_uint8 * 4)(*cls.MAGIC)  # pylint: disable=W0201
            instance.order = order  # pylint: disable=W0201
            instance.bytes = bytes  # pylint: disable=W0201
            return instance

    class Cursor():
        """The cursor of a line

        Attributes:
            serial(int): serial number, start from 1
            offset(int): start position of the line
            length(int): the length of data in the line
        """

        def __init__(self, handle: BinaryIO, serial: int, offset: int, content: bytes):  # noqa:E501
            length: int = len(content)
            if not (serial == 0 and offset == 0 and content == b""):
                self.check(serial, offset, length)
            self.__handle: BinaryIO = handle
            self.__serial: int = serial
            self.__offset: int = offset
            self.__length: int = length
            self.__content: bytes = content

        def __str__(self):
            return f"{__class__.__name__}(serial={self.serial}, offset={self.offset}, length={self.length})"  # noqa:E501

        def __bool__(self):
            return self.serial > 0

        @property
        def handle(self) -> BinaryIO:
            return self.__handle

        @property
        def serial(self) -> int:
            return self.__serial

        @property
        def offset(self) -> int:
            return self.__offset

        @property
        def length(self) -> int:
            return self.__length

        @property
        def content(self) -> bytes:
            return self.__content

        @property
        def prev_tail_offset(self) -> int:
            """the start position of prev metadata"""
            if self.serial <= 1:
                raise StopIteration("This is already the first line")

            return self.offset - LineFile.Metadata.SINGLE

        @property
        def next_head_offset(self) -> int:
            "the start position of next and the end position of current"
            return self.offset + self.length + LineFile.Metadata.DOUBLE if self.serial > 0 else 0  # noqa:E501

        def prev(self, content: bytes):
            if (serial := self.serial - 1) < 1:
                raise StopIteration("This is already the first line")

            offset: int = self.offset - len(content) - LineFile.Metadata.DOUBLE  # noqa:E501
            return LineFile.Cursor(self.handle, serial, offset, content)

        def next(self, content: bytes):
            return LineFile.Cursor(self.handle, self.serial + 1, self.next_head_offset, content)  # noqa:E501

        @classmethod
        def check(cls, serial: int, offset: int, length: int):
            if not LineFile.Metadata.check_order(serial):
                raise ValueError(f"Invalid serial: {serial}")

            if not LineFile.Metadata.check_bytes(length):
                raise ValueError(f"Invalid length: {length}")

            if offset < (LineFile.Metadata.DOUBLE + 1) * (serial - 1) or (serial == 1 and offset != 0):  # noqa:E501
                raise ValueError(f"Invalid offset: {offset} (serial {serial})")

        @classmethod
        def begin(cls, handle: BinaryIO):
            return cls(handle=handle, serial=0, offset=0, content=b"")

    def __init__(self, filepath: str, readonly: bool = True) -> None:
        super().__init__(filepath=filepath, readonly=readonly)
        assert super().open() is self.binary, "open failed"
        self.__cursor: LineFile.Cursor = self.check()

    def __len__(self) -> int:
        return self.__cursor.serial

    def __iter__(self) -> Iterator[Cursor]:
        """Default iterator is backward generator"""
        return self.backward()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().close()

    def __write(self, cursor: Cursor):
        if cursor.handle.tell() != cursor.offset or cursor.handle.seek(cursor.offset, 0) != cursor.offset:  # noqa:E501
            raise Warning(f"file position {cursor.handle.tell()} != {cursor.offset}")  # noqa:E501, pragma: no cover
        meta = bytes(self.Metadata.new(order=cursor.serial, bytes=cursor.length))  # noqa:E501
        assert cursor.handle.write(meta + cursor.content + meta) == cursor.length + LineFile.Metadata.DOUBLE  # noqa:E501

    def __read_next(self, current: Cursor) -> Cursor:
        serial: int = current.serial + 1
        offset: int = current.next_head_offset
        assert current.handle.seek(offset, 0) == offset

        head = self.Metadata.parse(current.handle.read(LineFile.Metadata.SINGLE))  # noqa:E501
        data: bytes = current.handle.read(head.bytes)
        tail = self.Metadata.parse(current.handle.read(LineFile.Metadata.SINGLE))  # noqa:E501
        if head != tail or head.order != serial:
            raise ValueError(f"serial: {serial}, {head} != {tail}")

        assert (endpos := current.handle.tell()) == offset + len(data) + LineFile.Metadata.DOUBLE, f"endpos({endpos}) error"  # noqa:E501
        return self.Cursor(current.handle, serial, offset, data)

    def __read_prev(self, current: Cursor) -> Cursor:
        if (serial := current.serial - 1) < 1:
            raise StopIteration("This is already the first line")  # noqa:E501, pragma: no cover

        endpos: int = current.offset
        offset: int = current.prev_tail_offset
        assert current.handle.seek(offset, 0) == offset
        tail = self.Metadata.parse(current.handle.read(LineFile.Metadata.SINGLE))  # noqa:E501

        offset -= LineFile.Metadata.SINGLE + tail.bytes
        assert current.handle.seek(offset, 0) == offset
        head = self.Metadata.parse(current.handle.read(LineFile.Metadata.SINGLE))  # noqa:E501
        data = current.handle.read(tail.bytes)
        assert current.handle.seek(LineFile.Metadata.SINGLE, 1) == endpos

        if head != tail or head.order != serial:
            raise ValueError(f"serial: {serial}, {head} != {tail}")
        return current.prev(data)

    def forward(self) -> Generator[Cursor, Any, None]:
        """Generate all lines in the file"""
        cursor = self.Cursor.begin(self.__cursor.handle)
        while cursor.next_head_offset <= self.__cursor.offset:
            cursor = self.__read_next(cursor)
            yield cursor

    def backward(self) -> Generator[Cursor, Any, None]:
        """Generate all lines in the file in reverse order"""
        cursor = self.__cursor
        while cursor.serial > 0:
            yield cursor
            if cursor.serial == 1:
                break
            cursor = self.__read_prev(cursor)

    def fast_check(self) -> Cursor:
        fhdl: BinaryIO = self.binary

        try:
            if (endpos := fhdl.tell()) <= LineFile.Metadata.DOUBLE:
                raise Warning(f"{endpos} <= {LineFile.Metadata.DOUBLE}")

            if fhdl.seek(-LineFile.Metadata.SINGLE, 2) != endpos - LineFile.Metadata.SINGLE:  # noqa:E501
                raise BufferError("seek overflow")  # pragma: no cover

            tail = self.Metadata.parse(fhdl.read(LineFile.Metadata.SINGLE))
            cursor = self.Cursor(fhdl, tail.order + 1, endpos, b"c")

            if (cursor := self.__read_prev(cursor)).next_head_offset != endpos:  # noqa:E501
                raise Warning("unexpected end of file")  # pragma: no cover
            return cursor
        except (ValueError, BufferError, Warning):
            return self.Cursor.begin(fhdl)

    def full_check(self) -> Cursor:
        cursor: LineFile.Cursor = self.Cursor.begin(fhdl := self.binary)

        try:
            while True:
                cursor = self.__read_next(cursor)
        except (ValueError, BufferError):
            assert fhdl.seek(endpos := cursor.next_head_offset, 0) == endpos, "seek failed"  # noqa:E501
            if not self.readonly:
                assert fhdl.truncate(endpos) == endpos, "truncate failed"

        return cursor

    def check(self) -> Cursor:
        return self.fast_check() or self.full_check()

    def append(self, datas: bytes) -> Cursor:
        if not self.readonly and len(datas) > 0:
            self.__write(cursor := self.__cursor.next(datas))
            self.__cursor = cursor
        return self.__cursor
