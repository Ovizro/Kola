import os
from typing import Any, Callable, Dict, Optional, Tuple, Union
from typing_extensions import Self

from ..writer import BaseWriter, FileWriter, StringWriter
from .command import Command
from .environment import EnvironmentEntry, EnvironmentExit
from .koilang import KoiLang


def _default_writer_factory(name: str):
    def inner(writer: BaseWriter, *args, **kwds) -> None:
        writer.write_command(name, *args, **kwds)
    return inner


class KoiLangWriter(KoiLang):
    def __init__(self, __writer: Union[str, bytes, os.PathLike, BaseWriter, None] = None) -> None:
        super().__init__()
        if __writer is None:
            self.writer = StringWriter(
                command_threshold=self.__class__.__command_threshold__
            )
        elif isinstance(__writer, BaseWriter):
            self.writer = __writer
        else:
            self.writer = FileWriter(
                __writer,
                command_threshold=self.__class__.__command_threshold__,
                encoding=self.__class__.__text_encoding__
            )
    
    def __kola_caller__(
        self,
        command: Command,
        args: tuple,
        kwargs: Dict[str, Any],
        *,
        envs: Tuple[str, ...] = (),
        writer_func: Optional[Callable] = None,
        **kwds: Any
    ) -> None:
        env_name = self.home.top.__class__.__name__
        if envs and env_name not in envs:
            raise ValueError(f"unmatched environment {env_name}")
        if command.__name__ in ["@start", "@end"]:
            # writer do not need to initalize
            return
        if isinstance(command, EnvironmentExit):
            self.writer.dec_indent()
        if not writer_func:
            if command.__name__ == "@text":
                writer_func = BaseWriter.write_text
            elif command.__name__ == "@annotation":
                writer_func = BaseWriter.write_annotation
            else:
                writer_func = _default_writer_factory(command.__name__)
        writer_func(self.writer, *args, **kwargs)
        if isinstance(command, EnvironmentEntry):
            self.writer.inc_indent()
    
    def getvalue(self) -> str:
        if not isinstance(self.writer, StringWriter):
            raise TypeError("only `StringWriter` object can use 'getvalue' method")
        return self.writer.getvalue()

    def __enter__(self) -> Self:
        self.writer.__enter__()
        return self

    def __exit__(self, *args) -> None:
        self.writer.__exit__(*args)
