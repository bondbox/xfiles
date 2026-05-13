# coding:utf-8

from os.path import isdir
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generic
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union


class Variable:

    def __init__(self, *args: Any, **kwargs: Any):
        self.__kargs: Dict[str, Any] = kwargs
        self.__pargs: List[Any] = [*args]

    def __iter__(self) -> Iterator[Any]:
        yield from self.__pargs

    def __getitem__(self, key: str) -> Any:
        return self.__kargs.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.__kargs[key] = value

    def duplicate(self, *args: Any, **kwargs: Any) -> "Variable":
        """Create a new Variable instance with copied args and kwargs.

        This allows modifications to the new instance without affecting
        the original.

        Args:
            *args: extend the original positional arguments
            **kwargs: override or extend the original keyword arguments

        Returns:
            A new Variable instance with shallow copies of args and kwargs,
            overridden by the provided arguments.
        """
        # **(self.__kargs | kwargs) needs Python 3.9+
        return Variable(*self.__pargs, *args, **{**self.__kargs, **kwargs})

    def populate(self, template: "Template") -> str:
        return template.format(*self.__pargs, **self.__kargs)


class Template:
    PRESET: str

    def __init__(self, text: Optional[str] = None):
        self.__text: Optional[str] = text

    @property
    def source(self) -> str:
        return self.__text or self.PRESET

    def format(self, *args, **kwargs) -> str:
        return self.source.format(*args, **kwargs)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Template":
        with open(path, "r", encoding="utf-8") as rhdl:
            return cls(text=rhdl.read())


TMKT = TypeVar("TMKT", str, Path)


class TemplateManager(Generic[TMKT]):

    def __init__(self, variable: Optional[Variable] = None):
        self.__variables: Variable = variable or Variable()
        self.__templates: Dict[TMKT, Template] = {}

    def __iter__(self) -> Iterator[Tuple[TMKT, Template]]:
        yield from self.__templates.items()

    def __getitem__(self, key: TMKT) -> Template:
        return self.__templates[key]

    def __setitem__(self, key: TMKT, template: Template):
        self.__templates[key] = template

    @property
    def variable(self) -> Variable:
        return self.__variables

    def evaluate(self, variable: Optional[Variable] = None) -> Iterator[Tuple[TMKT, str]]:  # noqa:E501
        variables: Variable = variable or self.variable
        for key, template in self.__templates.items():
            yield key, variables.populate(template)


TemplateManagerStr = TemplateManager[str]


class TemplateManagerPath(TemplateManager[Path]):

    def load(self, base: Union[str, Path]) -> None:
        for key, tpl in self.scan(base):
            self[key] = tpl

    @classmethod
    def scan(cls, base: Union[str, Path]) -> Iterator[Tuple[Path, Template]]:
        if not isdir(base):
            raise ValueError(f"Invalid path: {base} is not a directory")

        for item in (root := Path(base)).rglob("*"):
            if item.is_file():
                yield item.relative_to(root), Template.from_file(item)
