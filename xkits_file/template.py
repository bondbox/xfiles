# coding:utf-8

from typing import Any
from typing import Dict
from typing import Iterator
from typing import List


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

    def set_default(self, key: str, value: Any) -> None:
        self.__kargs.setdefault(key, value)

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
        return Variable(*self.__pargs, *args, **(self.__kargs | kwargs))
