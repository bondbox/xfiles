# coding:utf-8

from typing import Optional
from typing import Sequence

from xkits_command import ArgParser
from xkits_command import Command
from xkits_command import CommandArgument
from xkits_command import CommandExecutor

from xkits_file.attribute import __urlhome__
from xkits_file.attribute import __version__
from xkits_fileviewer.linefile import add_cmd as add_cmd_line


@CommandArgument("fileviewer", description="xkits file viewer")
def add_cmd(_arg: ArgParser):  # pylint: disable=unused-argument
    pass


@CommandExecutor(add_cmd, add_cmd_line)
def run_cmd(cmds: Command) -> int:  # pylint: disable=unused-argument
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = Command()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv, epilog=f"For more, please visit {__urlhome__}.")  # noqa:E501
