import os
from types import TracebackType
from typing import Any, Dict, Final, List, Type, Union
from typing_extensions import Protocol, runtime_checkable, Self


WF_BASE_ITEM: int
WF_COMPLEX_ITEM: int
WF_ARG_ITEM: int
WF_FULL_CMD: int


@runtime_checkable
class WriterItemLike(Protocol):
    def __kola_write__(self, __writer: BaseWriter, __level: int) -> None: ...


class BaseWriterItem(object):
    def __kola_write__(self, writer: BaseWriter, level: int) -> None: ...


class FormatItem(BaseWriterItem):
    value: Final[Any]
    spec: Final[str]

    def __init__(self, value: Any, spec: str) -> None: ...


class ComplexArg(BaseWriterItem):
    name: Final[str]
    value: Final[Any]

    def __init__(self, name: str, value: Any, *, split_line: bool = ...) -> None: ...


WI_NEWLINE: BaseWriterItem


_BaseItem = Union[str, bytes, int, float, WriterItemLike]
_ComplexItem = Union[_BaseItem, List[_BaseItem], Dict[str, _BaseItem]]


class BaseWriter(object):
    indent: Final[int]

    def __init__(self, indent: int = 4, command_threshold: int = 1) -> None: ...
    def raw_write(self, text: str) -> None: ...
    def close(self) -> None: ...
    def inc_indent(self) -> None: ...
    def dec_indent(self) -> None: ...
    def newline(self, concat_prev: bool = ...) -> None: ...
    def write_text(self, text: str) -> None: ...
    def write_annotation(self, annotation: str) -> None: ...
    def write_command(self, __name: Union[str, int], *args: _BaseItem, **kwds: _ComplexItem) -> None: ...
    def write(self, command: Union[str, WriterItemLike]) -> None: ...
    @property
    def closed(self) -> bool: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, exc_type: Type[BaseException], exc_ins: Exception, traceback: TracebackType) -> None: ...


class FileWriter(BaseWriter):
    path: Final[Union[str, bytes, os.PathLike]]
    encoding: Final[str]

    def __init__(self, __path: Union[str, bytes, os.PathLike], encoding: str = "utf-8",
                 indent: int = ..., command_threshold: int = ...) -> None: ...


class StringWriter(BaseWriter):
    def getvalue(self) -> str: ...
