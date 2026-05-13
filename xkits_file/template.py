# coding:utf-8

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
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
