# coding:utf-8

from typing import Optional
from typing import Sequence

from xkits_command import ArgParser
from xkits_command import Command
from xkits_command import CommandArgument
from xkits_command import CommandExecutor

from xkits_file.attribute import __urlhome__
from xkits_file.attribute import __version__
from xkits_file.linefile import LineFile


@CommandArgument("line", description="xkits line file viewer")
def add_cmd(_arg: ArgParser):  # pylint: disable=unused-argument
    _arg.add_opt_on("-r", "--reverse", dest="reverse",
                    help="Reverse the order of the lines")
    _arg.add_argument("-e", dest="encoding", type=str,
                      help="The encoding with which to decode the bytes",
                      nargs="?", const="utf-8", metavar="ENCODING")
    _arg.add_argument(dest="file", type=str, help="Line file path",
                      metavar="PATH")


@CommandExecutor(add_cmd)
def run_cmd(cmds: Command) -> int:  # pylint: disable=unused-argument
    path: str = cmds.args.file
    reverse: bool = cmds.args.reverse
    encoding: Optional[str] = cmds.args.encoding
    with LineFile(filepath=path, readonly=True) as line:
        for item in (line.backward() if reverse else line.forward()):
            cmds.stdout(item.content.decode(encoding) if encoding else item.content)  # noqa:E501
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    cmds = Command()
    cmds.version = __version__
    return cmds.run(root=add_cmd, argv=argv, epilog=f"For more, please visit {__urlhome__}.")  # noqa:E501
