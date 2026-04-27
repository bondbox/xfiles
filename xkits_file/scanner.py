# coding:utf-8

from os import cpu_count
from os import listdir
from os import lstat
from os import stat
from os import stat_result
from os.path import abspath
from os.path import exists
from os.path import isdir
from os.path import islink
from os.path import join
from os.path import normpath
from os.path import realpath
from os.path import relpath
from pathlib import Path
from queue import Empty
from queue import Queue
from stat import S_ISDIR
from stat import S_ISLNK
from stat import S_ISREG
from threading import Thread
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

CPU_COUNT = cpu_count()
THDNUM_MINIMUM = 1
THDNUM_MAXIMUM = CPU_COUNT if isinstance(CPU_COUNT, int) else 64
THDNUM_DEFAULT = int(THDNUM_MAXIMUM / 2)


class Scanner:
    """scan file objects"""

    class Object:  # pylint: disable=too-many-public-methods

        def __init__(self, path: Union[str, Path]):
            assert isinstance(path, (str, Path))
            self.__path: Path = Path(normpath(path))
            self.__abspath: Path = Path(abspath(self.__path))
            self.__realpath: Path = Path(realpath(self.__abspath))

        @property
        def path(self) -> Path:
            return self.__path

        @property
        def abspath(self) -> Path:
            return self.__abspath

        @property
        def realpath(self) -> Path:
            return self.__realpath

        @property
        def stat(self) -> stat_result:
            return stat(self.abspath)

        @property
        def lstat(self) -> stat_result:
            return lstat(self.abspath)

        @property
        def uid(self) -> int:
            """user id of owner"""
            return self.stat.st_uid

        @property
        def gid(self) -> int:
            """group id of owner"""
            return self.stat.st_gid

        @property
        def mode(self) -> int:
            return self.stat.st_mode

        @property
        def ctime(self) -> float:
            return self.stat.st_ctime

        @property
        def atime(self) -> float:
            """time of most recent access"""
            return self.stat.st_atime

        @property
        def mtime(self) -> float:
            """time of most recent content modification"""
            return self.stat.st_mtime

        @property
        def size(self) -> int:
            return self.stat.st_size

        @property
        def isdir(self) -> bool:
            return S_ISDIR(self.stat.st_mode)

        @property
        def isreg(self) -> bool:
            return S_ISREG(self.stat.st_mode)

        @property
        def isfile(self) -> bool:
            return self.isreg

        @property
        def islink(self) -> bool:
            return S_ISLNK(self.lstat.st_mode)

        @property
        def issym(self) -> bool:
            return self.islink

        def hash(self, *args, chunk=1048576) -> Tuple[str, ...]:
            assert self.isfile and not self.issym
            with open(self.abspath, "rb") as fhandler:
                while True:
                    data = fhandler.read(chunk)
                    if not data:
                        break
                    for _hash in args:
                        _hash.update(data)
            return tuple(_hash.hexdigest() for _hash in args)

    def __init__(self):
        self.__objdict: Dict[Path, Scanner.Object] = {}
        self.__objects: Set[Scanner.Object] = set()
        self.__objsyms: Set[Scanner.Object] = set()
        self.__objregs: Set[Scanner.Object] = set()
        self.__objdirs: Set[Scanner.Object] = set()

    def __iter__(self):
        return iter(self.__objects)

    def __getitem__(self, key: Union[str, Path]):
        return self.__objdict[Path(key)]

    @property
    def dirs(self) -> Set[Object]:
        return self.__objdirs

    @property
    def files(self) -> Set[Object]:
        return self.__objregs

    @property
    def links(self) -> Set[Object]:
        return self.__objsyms

    def add(self, obj: Object):
        assert isinstance(obj, Scanner.Object)
        if obj.path not in self.__objdict:
            self.__objdict[obj.path] = obj
            self.__objects.add(obj)
            if obj.issym:
                self.__objsyms.add(obj)
            if obj.isdir:
                self.__objdirs.add(obj)
            elif obj.isreg:
                self.__objregs.add(obj)

    @classmethod
    def load(cls,  # pylint: disable=R0913,R0914,R0915,R0917
             paths: Sequence[str],
             exclude: Optional[Sequence[str]] = None,
             linkdir: bool = True,
             threads: int = THDNUM_DEFAULT,
             handler: Optional[Callable[[Object], bool]] = None):
        if exclude is None:
            exclude = []

        assert isinstance(paths, Sequence)
        assert isinstance(exclude, Sequence)
        assert isinstance(linkdir, bool)
        assert isinstance(threads, int)

        thds = min(max(THDNUM_MINIMUM, threads), THDNUM_MAXIMUM)

        def rpath(path: Union[str, Path]) -> Path:
            assert isinstance(path, (str, Path))
            return Path(relpath(path))

        # filter files and directorys
        def path_filter() -> Set[Path]:
            filter_paths: Set[Path] = set()

            for path in exclude:
                filter_paths.add(rpath(path))

            return filter_paths

        class task_stat:  # pylint: disable=too-few-public-methods

            def __init__(self):
                self.exit = False
                self.handler = handler
                self.scanner = Scanner()
                self.filter: Set[Path] = path_filter()
                self.q_path: "Queue[Path]" = Queue()
                self.q_task: "Queue[Scanner.Object]" = Queue(maxsize=thds * 2)

        scan_stat = task_stat()

        def task_scan_path():
            scanned_dirs = set()
            while not scan_stat.exit or not scan_stat.q_path.empty():
                try:
                    path = scan_stat.q_path.get(timeout=0.01)
                except Empty:
                    continue

                path = rpath(path)
                assert isinstance(path, Path)

                if path in scan_stat.filter or not exists(path):
                    scan_stat.q_path.task_done()
                    continue

                if isdir(path) and path not in scanned_dirs:
                    scanned_dirs.add(path)
                    # scan symbolic link dirs?
                    if not islink(path) or linkdir:
                        for sub in listdir(path=path):
                            spath = join(path, sub)
                            scan_stat.q_path.put(Path(spath))

                ret = True
                obj = Scanner.Object(path)

                if isinstance(scan_stat.handler, Callable):
                    ret = scan_stat.handler(obj)
                    assert isinstance(ret, bool)

                if ret is True:
                    scan_stat.q_task.put(obj)
                scan_stat.q_path.task_done()

        def task_scan():
            while not scan_stat.exit or not scan_stat.q_task.empty():
                try:
                    obj = scan_stat.q_task.get(timeout=0.01)
                except Empty:
                    continue

                scan_stat.scanner.add(obj=obj)
                scan_stat.q_task.task_done()

        task_threads: List[Thread] = []
        task_threads.append(Thread(target=task_scan, name="xkits-scan"))
        task_threads.extend([
            Thread(target=task_scan_path, name=f"xkits-scan{i}")
            for i in range(thds)
        ])

        for thread in task_threads:
            thread.start()

        for path in paths:
            scan_stat.q_path.put(Path(path))

        scan_stat.q_path.join()
        scan_stat.q_task.join()
        scan_stat.exit = True

        for thread in task_threads:
            thread.join()

        return scan_stat.scanner
