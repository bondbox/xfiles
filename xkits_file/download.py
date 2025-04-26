# coding=utf-8

from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import isdir
from os.path import isfile
from os.path import join
from typing import Optional

from xkits_lib import TimeUnit
from xkits_logger import Logger

from xkits_file.filestat import FileStat


class Downloader:
    """File downloader

    Download file from url, and save to temp file first. Move the temp file
    to final path when complete. If download failed, only cleanup temp file
    is needed. This can simplify the check and cleanup process without more
    space requirement.
    """

    def __init__(self, url: str, path: Optional[str] = None,
                 timeout: TimeUnit = 180, chunk_size: int = 1048576):
        def parse(url: str, path: Optional[str]) -> str:
            if not path:
                return basename(url.rstrip("/"))

            if exists(path) and isdir(path):
                return join(path, basename(url.rstrip("/")))

            return path

        self.__chunk_size: int = min(max(4096, chunk_size), 8388608)  # 4K ~ 8M
        self.__timeout: float = float(timeout)
        self.__path: str = parse(url, path)
        self.__url: str = url

    @property
    def url(self) -> str:
        return self.__url

    @property
    def path(self) -> str:
        return self.__path

    @property
    def temp(self) -> str:
        return f"{self.path}.tmp"

    @property
    def stat(self) -> FileStat:
        return FileStat(self.path)

    @property
    def timeout(self) -> float:
        return self.__timeout

    @property
    def chunk_size(self) -> int:
        return self.__chunk_size

    def prepare(self) -> bool:
        """Prepare to download file

        This method will:
            1. raise FileExistsError if file already exists
            2. os.makedis() to create folder if not exists
            3. return False if cannot download new file
            4. cleanup temp file before download
        """
        if exists(self.path):
            if not isfile(self.path):
                Logger.stdout_red(f"Path '{self.path}' is not a file")
                return False
            raise FileExistsError(f"File '{self.path}' already exists")

        if (folder := dirname(self.path)) and not exists(folder):
            from os import makedirs  # pylint:disable=import-outside-toplevel

            makedirs(folder)

        return self.cleanup()

    def cleanup(self) -> bool:
        """Cleanup downloaded temp file"""
        if exists(temp := self.temp) and isfile(temp):
            from os import remove  # pylint:disable=import-outside-toplevel

            remove(temp)

        return not exists(temp)

    def complete(self) -> bool:
        """Move temp file to final path and check when complete"""
        from shutil import move  # pylint: disable=import-outside-toplevel

        if exists(temp := self.temp) and isfile(temp) and move(src=temp, dst=self.path) != self.path:  # noqa:E501
            raise Warning(f"Cannot move '{temp}' to '{self.path}")  # noqa:E501, pragma: no cover
        Logger.stdout_green(f"Download '{self.url}' to '{self.path}' completed")  # noqa:E501

        return exists(self.path) and isfile(self.path)

    def start(self) -> bool:
        from os import fsync  # pylint:disable=import-outside-toplevel

        from requests import ConnectionError  # pylint:disable=C0415,W0622
        from requests import HTTPError  # pylint:disable=C0415
        from requests import get  # noqa:H306, pylint:disable=C0415

        if self.prepare():
            try:
                with get(self.url, timeout=self.timeout, stream=True) as response:  # noqa:E501
                    response.raise_for_status()  # HTTPError
                    with open(self.temp, "wb") as whdl:
                        Logger.stdout_yellow(f"Download '{self.url}' to '{self.path}' started")  # noqa:E501
                        for chunk in response.iter_content(chunk_size=self.chunk_size):  # noqa:E501
                            if not chunk:
                                raise ValueError("Empty chunk received")  # noqa:E501, pragma: no cover
                            whdl.write(chunk)
                        fsync(whdl)
            except (ConnectionError, HTTPError) as e:
                Logger.stdout_red(f"Failed to download '{self.url}' to '{self.path}': {e}")  # noqa:E501
                self.cleanup()
                return False

        return self.complete()
