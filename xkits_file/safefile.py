# coding=utf-8

from io import BufferedRandom
from io import BufferedReader
from io import TextIOWrapper
import os
from typing import Any
from typing import BinaryIO
from typing import IO
from typing import Optional
from typing import TextIO


class SafeKits:

    @classmethod
    def lock(cls, origin: str):
        """Unified file lock"""
        from filelock import FileLock  # pylint: disable=C0415

        return FileLock(f"{origin}.lock")

    @classmethod
    def get_backup_path(cls, origin: str) -> str:
        """Unified backup path"""
        return f"{origin}.bak"

    @classmethod
    def create_backup(cls, path: str, copy: bool = False) -> bool:
        """Create a backup before writing file

        Backup files with '.bak' suffix will be created in the same directory.
        By default shutil.move() is used to create the backup file, which will
        use os.rename() to rename the original file. This will make the backup
        very efficient.
        But, if you wish to append to the original file, you need to specify
        'copy=True' to use shutil.copy2().
        """
        if os.path.exists(pbak := cls.get_backup_path(path)):
            return False
        if not os.path.exists(path):  # No need for backup
            return True
        assert os.path.isfile(path), f"'{path}' is not a regular file"

        import shutil  # pylint: disable=import-outside-toplevel

        method = shutil.copy2 if copy else shutil.move
        assert method(src=path, dst=pbak) == pbak, f"backup '{path}' failed"
        return os.path.exists(pbak)

    @classmethod
    def delete_backup(cls, path: str) -> bool:
        """Delete backup after writing file"""
        if os.path.isfile(pbak := cls.get_backup_path(path)):
            os.remove(pbak)
        return not os.path.exists(pbak)

    @classmethod
    def restore(cls, path: str) -> bool:
        """Restore (if backup exists) before reading file"""
        pbak: str = cls.get_backup_path(path)
        if os.path.isfile(pbak):
            if os.path.isfile(path):
                os.remove(path)

            import shutil  # pylint: disable=import-outside-toplevel

            assert not os.path.exists(path), f"file '{path}' still exists"
            assert shutil.move(src=pbak, dst=path) == path, \
                f"restore backup file '{pbak}' to '{path}' failed"
        return not os.path.exists(pbak)


class BaseFile():

    def __init__(self, filepath: str, readonly: bool = True, encoding: Optional[str] = None) -> None:  # noqa:E501
        self.__fhandler: Optional[IO[Any]] = None
        self.__encoding: Optional[str] = encoding
        self.__readonly: bool = readonly
        self.__filepath: str = filepath

        if readonly and not os.path.exists(filepath):
            # When the file is writable, create it if not exists
            raise FileNotFoundError(f"file '{filepath}' does not exist")

    def __del__(self):
        self.close()

    def __enter__(self) -> IO[Any]:
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def filepath(self) -> str:
        return self.__filepath

    @property
    def readonly(self) -> bool:
        return self.__readonly

    @property
    def encoding(self) -> Optional[str]:
        return self.__encoding

    @property
    def fhandler(self) -> Optional[IO[Any]]:
        return self.__fhandler

    @property
    def binary(self) -> BinaryIO:
        if not self.__fhandler or not isinstance(self.__fhandler, BufferedReader if self.readonly else BufferedRandom):  # noqa:E501
            raise TypeError(f"file handler({type(self.__fhandler)}) is not a binary file")  # noqa:E501
        return self.__fhandler

    @property
    def text(self) -> TextIO:
        if not self.__fhandler or not isinstance(self.__fhandler, TextIOWrapper):  # noqa:E501
            raise TypeError(f"file handler({type(self.__fhandler)}) is not a text file")  # noqa:E501
        return self.__fhandler

    def open(self) -> IO[Any]:
        def readonly_mode() -> str:
            return "r" if self.encoding else "rb"

        def writable_mode() -> str:
            return "a+" if self.encoding else "ab+"

        if self.__fhandler is None:
            mode: str = readonly_mode() if self.readonly else writable_mode()
            self.__fhandler = open(self.filepath, mode, encoding=self.encoding)  # noqa:E501 pylint: disable=consider-using-with

        return self.__fhandler

    def close(self) -> None:
        if self.__fhandler is not None:
            self.__fhandler.close()
            self.__fhandler = None

    def sync(self):
        if self.__fhandler is not None and not self.readonly:
            os.fsync(self.__fhandler)


class SafeFile(BaseFile):

    def backup(self, copy: bool = False) -> None:
        offset: int = self.fhandler.tell() if self.fhandler else -1

        super().close()

        if not SafeKits.create_backup(self.filepath, copy=copy):
            raise Warning(f"failed to backup '{self.filepath}'")

        if offset >= 0 and not (self.readonly and not copy):
            self.open().seek(offset if copy else 0)

    def restore(self) -> None:
        reopen: bool = self.fhandler is not None
        super().close()

        if not SafeKits.restore(self.filepath):
            raise Warning(f"failed to restore '{self.filepath}'")

        if reopen:
            self.open()
