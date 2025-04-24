# coding=utf-8

import os
from typing import Union


class FileStat:
    """File attributes and permissions

    Manage file owner, group and permissions.
    """

    def __init__(self, path: str):
        self.__path: str = path

    @property
    def path(self) -> str:
        return self.__path

    @property
    def stat(self) -> os.stat_result:
        """file stat"""
        return os.stat(self.path)

    @property
    def uid(self) -> int:
        """file uid"""
        return self.stat.st_uid

    @uid.setter
    def uid(self, uid: int):
        """change file uid"""
        os.chown(self.path, uid, -1)

    @property
    def gid(self) -> int:
        """file gid"""
        return self.stat.st_gid

    @gid.setter
    def gid(self, gid: int):
        """change file gid"""
        os.chown(self.path, -1, gid)

    @property
    def username(self) -> str:
        """file owner"""
        try:
            from pwd import getpwuid  # pylint:disable=import-outside-toplevel
            return getpwuid(self.uid).pw_name
        except KeyError:  # pragma: no cover
            return str(self.uid)  # pragma: no cover

    @username.setter
    def username(self, owner: Union[int, str]):
        """change file owner"""
        from pwd import getpwnam  # pylint:disable=import-outside-toplevel
        self.uid = getpwnam(owner).pw_uid if isinstance(owner, str) else owner

    @property
    def groupname(self) -> str:
        """file group"""
        try:
            from grp import getgrgid  # pylint:disable=import-outside-toplevel
            return getgrgid(self.gid).gr_name
        except KeyError:  # pragma: no cover
            return str(self.gid)  # pragma: no cover

    @groupname.setter
    def groupname(self, group: Union[int, str]):
        """change file group"""
        from grp import getgrnam  # pylint:disable=import-outside-toplevel
        self.gid = getgrnam(group).gr_gid if isinstance(group, str) else group

    def chown(self, owner: Union[int, str], group: Union[int, str] = -1):
        """change file owner and group"""
        self.username = int(owner) if isinstance(owner, str) and owner.isdigit() else owner  # noqa:E501
        self.groupname = int(group) if isinstance(group, str) and group.isdigit() else group  # noqa:E501

    def chgrp(self, group: Union[int, str]):
        """change group ownership"""
        self.groupname = int(group) if isinstance(group, str) and group.isdigit() else group  # noqa:E501

    @property
    def mode(self) -> str:
        """file mode bits

        6 bits octal digits, e.g. 100644, 040755:

            040764 (drwxrw-r--)
            ┣┛┃┃┃┃
            ┃ ┃┃┃┗━━ Other  ━┓
            ┃ ┃┃┗━━━ Group   ┣━ Permissions
            ┃ ┃┗━━━━ Owner  ━┛
            ┃ ┗━━━━━ Special (setuid, setgid, sticky) Permissions
            ┗━━━━━━━ File type

        File type:

            | 0o140000 | S_IFSOCK | socket            |
            | 0o120000 | S_IFLNK  | symbolic link     |
            | 0o100000 | S_IFREG  | regular file      |
            | 0o060000 | S_IFBLK  | block device      |
            | 0o040000 | S_IFDIR  | directory         |
            | 0o020000 | S_IFCHR  | character device  |
            | 0o010000 | S_IFIFO  | FIFO              |

        Permissions:

            | 7 | rwx | read, write, execute            |
            | 6 | rw- | read, write                     |
            | 5 | r-x | read, execute                   |
            | 4 | r-- | read                            |
            | 3 | -wx | write, execute                  |
            | 2 | -w- | write                           |
            | 1 | --x | execute                         |
            | 0 | --- | no read, no write, no execute   |

        Example:
            stfile("example.txt").mode # 100644
            stfile("example.txt").mode[-4:] # 0755
            stfile("example.txt").mode[-3:] # 764
        """
        return oct(self.stat.st_mode)[2:].rjust(6, "0")

    @property
    def human_mode(self) -> str:
        """file mode in `ls -l` format

        10 bits characters, e.g. -rw-r--r--, lrw-rw----, drwxrwxrwx:

             ┏━━━━━━━━━━ Read permission: -/r
             ┃┏━━━━━━━━━ Write permission: -/w
             ┃┃┏━━━━━━━━ Execute permission: -/x/s(x + SUID)/S(only SUID)
             ┃┃┃
             ┃┃┃┏━━━━━━━ Read permission: -/r
             ┃┃┃┃┏━━━━━━ Write permission: -/w
             ┃┃┃┃┃┏━━━━━ Execute permission: -/x/s(x + SGID)/S(only SGID)
             ┃┃┃┃┃┃
             ┃┃┃┃┃┃┏━━━━ Read permission: -/r
             ┃┃┃┃┃┃┃┏━━━ Write permission: -/w
             ┃┃┃┃┃┃┃┃┏━━ Execute permission: -/x/t(x + SBIT)/T(only SBIT)
            -rwxr-xr-x (100755)
            ┃┗┳┛┗┳┛┗┳┛
            ┃ ┃  ┃  ┗━━━ Other  ━┓
            ┃ ┃  ┗━━━━━━ Group   ┣━ Permissions
            ┃ ┗━━━━━━━━━ Owner  ━┛
            ┗━━━━━━━━━━━ File type
        """
        import stat  # pylint:disable=import-outside-toplevel
        return stat.filemode(self.stat.st_mode)

    @property
    def human_file_type(self) -> str:
        """File type

        4 (13 - 16 bits) file type bitmask:

            | - | regular file      | stat.S_ISREG  | S_IFREG   | 0o100000 |
            | d | directory         | stat.S_ISDIR  | S_IFDIR   | 0o040000 |
            | l | symbolic link     | stat.S_ISLNK  | S_IFLNK   | 0o120000 |
            | b | block device      | stat.S_ISBLK  | S_IFBLK   | 0o060000 |
            | c | character device  | stat.S_ISCHR  | S_IFCHR   | 0o020000 |
            | s | socket            | stat.S_ISSOCK | S_IFSOCK  | 0o140000 |
            | p | FIFO              | stat.S_ISFIFO | S_IFIFO   | 0o010000 |
        """
        return self.human_mode[0]

    @property
    def human_all_permissions(self) -> str:
        """File all users permissions

        9 (1 - 9 bits) users permissions bitmask and
        3 (10 - 12 bits) special permissions
        """
        return self.human_mode[-9:]

    @property
    def human_owner_permissions(self) -> str:
        """File owner permissions

        3 (7 - 9 bits) owner permissions bitmask and setuid bit:
            - Read permission: -/r
            - Write permission: -/w
            - Execute permission: -/x/s(x + SUID)/S(only SUID)
        """
        return self.human_all_permissions[0:3]

    @property
    def human_group_permissions(self) -> str:
        """File group permissions

        3 (4 - 6 bits) group permissions bitmask and setgid bit:
            - Read permission: -/r
            - Write permission: -/w
            - Execute permission: -/x/s(x + SGID)/S(only SGID)
        """
        return self.human_all_permissions[3:6]

    @property
    def human_other_permissions(self) -> str:
        """File other (not in group) permissions

        3 (1 - 3 bits) other permissions bitmask and sticky bit:
            - Read permission: -/r
            - Write permission: -/w
            - Execute permission: -/x/t(x + SBIT)/T(only SBIT)
        """
        return self.human_all_permissions[6:9]

    def chmod(self, mode: Union[int, str]):
        """change file mode bits"""
        if isinstance(mode, str):
            mode = int(mode, 8)
        os.chmod(self.path, mode)
