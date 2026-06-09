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
        return self.__text if isinstance(self.__text, str) else self.PRESET

    def format(self, *args, **kwargs) -> str:
        return self.source.format(*args, **kwargs)

    @classmethod
    def load(cls, filepath: Union[str, Path]) -> "Template":
        with open(filepath, "r", encoding="utf-8") as rhdl:
            return cls(text=rhdl.read())

    def save(self, filepath: Union[str, Path], variable: Optional[Variable] = None) -> None:  # noqa:E501
        text: str = variable.populate(self) if isinstance(variable, Variable) else self.source  # noqa:E501

        if not isinstance(filepath, Path):
            filepath = Path(filepath)

        if not (parent := filepath.parent).exists():
            parent.mkdir(parents=True)

        with open(filepath, "w", encoding="utf-8") as whdl:
            whdl.write(text)


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
        for key, tpl in self.__templates.items():
            yield key, variables.populate(tpl)


TemplateManagerStr = TemplateManager[str]


class TemplateManagerPath(TemplateManager[Path]):

    @classmethod
    def scan(cls, base: Union[str, Path]) -> Iterator[Tuple[Path, Template]]:
        if not isdir(root := base if isinstance(base, Path) else Path(base)):
            raise ValueError(f"Invalid path: {root} is not a directory")

        for item in root.rglob("*"):
            if item.is_file() and "__pycache__" not in item.parts:
                yield item.relative_to(root), Template.load(item)

    def load(self, base: Union[str, Path]) -> None:
        for name, tmpl in self.scan(base):
            self[name] = tmpl

    def dump(self, base: Union[str, Path], variable: Optional[Variable] = None, writable: bool = False) -> None:  # noqa:E501
        root: Path = base if isinstance(base, Path) else Path(base)
        variables: Variable = variable or self.variable

        for name, tmpl in iter(self):
            if not (path := root / name).exists() or writable:
                tmpl.save(filepath=path, variable=variables)
