import os
from inspect import signature, Signature
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union
from typing_extensions import Self

from ..writer import BaseWriter, FileWriter, StringWriter
from .command import Command
from .environment import Environment
from .handler import AbstractHandler
from .koilang import KoiLang


@lru_cache()
def _default_writer_factory(name: str, sig: Optional[Signature] = None):
    if name == "@text":
        return BaseWriter.write_text
    elif name == "@annotation":
        return BaseWriter.write_annotation

    def inner(writer: BaseWriter, *args, **kwds) -> None:
        if sig:
            # check writer arguments
            sig.bind(writer, *args, **kwds)
        if name != "@number":
            args = (name,) + args
        writer.write_command(*args, **kwds)
    return inner


class KoiLangWriter(KoiLang):
    """
    writer class for the KoiLang class

    The class should not be used directly.
    The usual way to use it is to call YourKoiLang.writer().
    """
    def __init__(self, ___writer: Union[str, bytes, os.PathLike, BaseWriter, None] = None) -> None:
        super().__init__()
        if ___writer is None:
            self._writer = StringWriter(
                command_threshold=self.__class__.__command_threshold__
            )
        elif isinstance(___writer, BaseWriter):
            self._writer = ___writer
        else:
            self._writer = FileWriter(
                ___writer,
                command_threshold=self.__class__.__command_threshold__,
                encoding=self.__class__.__text_encoding__
            )
    
    def push_apply(self, __push_cache: Environment) -> None:
        self._writer.inc_indent()
        return super().push_apply(__push_cache)
    
    def pop_prepare(self, __env_type: Optional[Type[Environment]] = None) -> Environment:
        self._writer.dec_indent()
        return super().pop_prepare(__env_type)
    
    def newline(self) -> None:
        self._writer.newline()
    
    def getvalue(self) -> str:
        if not isinstance(self._writer, StringWriter):  # pragma: no cover
            raise TypeError("only `StringWriter` object can use 'getvalue' method")
        return self._writer.getvalue()

    def __enter__(self) -> Self:
        self._writer.__enter__()
        return self

    def __exit__(self, *args) -> None:
        return self._writer.__exit__(*args)


@KoiLangWriter.register_handler
class WriterHandler(AbstractHandler):
    __slots__ = []

    priority = 3
    owner: "KoiLangWriter"

    def __call__(
        self,
        command: Command,
        args: Tuple,
        kwargs: Dict[str, Any],
        *,
        writer_func: Optional[Callable] = None,
        **kwds: Any
    ) -> Any:
        name = command.__name__
        if name.startswith('@') and name not in ["@text", "@number", "@annotation"]:  # pragma: no cover
            return super().__call__(command, args, kwargs, **kwds)
        
        if not writer_func:
            writer_func = _default_writer_factory(
                command.__name__, signature(command.__func__)
            )
        return writer_func(self.owner._writer, *args, **kwargs)
