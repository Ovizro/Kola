import os
import sys
from types import MethodType, TracebackType
from typing import Any, Callable, Dict, Generator, Optional, Tuple, Type, TypeVar, Union, overload
from typing_extensions import Literal

from ..lexer import BaseLexer, FileLexer, StringLexer
from ..parser import Parser
from ..exception import KoiLangError
from .commandset import Command, CommandSetMeta, CommandSet
from .environment import Environment


_T_EnvCls = TypeVar("_T_EnvCls", bound=Type[Environment])


class KoiLangMeta(CommandSetMeta):
    """
    metaclass for KoiLang class

    Provide encoding and command threshold support.
    """
    __text_encoding__: str
    __command_threshold__: int

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any],
                command_threshold: int = 0, encoding: Optional[str] = None, **kwds: Any):
        has_base = any(isinstance(i, cls) for i in bases)
        if command_threshold or not has_base:
            assert command_threshold >= 0
            attr["__command_threshold__"] = command_threshold or 1
        if encoding or not has_base:
            attr["__text_encoding__"] = encoding or "utf-8"
        return super().__new__(cls, name, bases, attr, **kwds)

    def register_environment(self, env_class: _T_EnvCls) -> _T_EnvCls:
        self.__command_field__.add(env_class)
        return env_class


class KoiLang(CommandSet, metaclass=KoiLangMeta):
    """
    main class for KoiLang virtual machine

    `KoiLang` class is a top-level interface of 'kola' package.
    Just create a subclass to define your own mackup language based on KoiLang.
    """
    __slots__ = ["__top"]

    def __init__(self) -> None:
        super().__init__()
        self.__top = self

    def __getitem__(self, __key: str) -> Callable:
        if self.__top is self:
            return super().__getitem__(__key)
        return self.__top[__key]

    def push(self, cmd_set: Environment) -> None:
        assert cmd_set.back is self.top
        self.__top = cmd_set

    def pop(self) -> Environment:
        top = self.__top
        if top is self:
            raise ValueError('cannot pop the inital environment')
        assert isinstance(top, Environment)
        self.__top = top.back
        return top

    @property
    def top(self) -> CommandSet:
        return self.__top

    @MethodType(Command, "@start")
    def at_start(self) -> None:
        """
        parser initalize command
        
        It is called before parsing start.
        """

    @MethodType(Command, "@end")
    def at_end(self) -> None:
        """
        parser finalize command
        
        It is called after parsing end. And the return value
        will be that of 'parse' method.
        """
    
    @MethodType(Command, "@exception")
    def on_exception(self, exc_ins: BaseException, exc_type: Type[BaseException], traceback: TracebackType) -> None:
        """
        exception handling command

        It is called when a KoiLang error occurs.
        If the command wishes to suppress the exception, it should a true value.
        """
    
    def __parse(self, __lexer: BaseLexer) -> None:
        self["@start"]()
        while True:
            try:
                # Parser.exec() is a fast C level loop.
                Parser(__lexer, self).exec()
            except KoiLangError:
                if not self["@exception"](*sys.exc_info()):
                    self["@end"]
                    raise
            else:
                break
        self["@end"]()
    
    def __parse_and_ret(self, __lexer: BaseLexer) -> Generator[Any, None, None]:
        self["@start"]()
        while True:
            try:
                yield from Parser(__lexer, self)
            except KoiLangError:
                if not self["@exception"](*sys.exc_info()):
                    self["@end"]()
                    raise
            else:
                break
        self["@end"]()

    @overload
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: Literal[False] = False) -> None: ...
    @overload
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: Literal[True]) -> Generator[Any, None, None]: ...
    
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: bool = False) -> Any:
        """
        Parse kola text or lexer from other method.
        """
        if isinstance(lexer, str):
            lexer = StringLexer(
                lexer,
                encoding=self.__class__.__text_encoding__,
                command_threshold=self.__class__.__command_threshold__
            )
        if with_ret:
            return self.__parse_and_ret(lexer)
        else:
            self.__parse(lexer)
        
    def parse_file(self, path: Union[str, bytes, os.PathLike], *, encoding: Optional[str] = None, **kwds: Any) -> Any:
        """
        Parse a kola file.
        """
        return self.parse(
            FileLexer(
                path, encoding=encoding or self.__class__.__text_encoding__,
                command_threshold=self.__class__.__command_threshold__
            ), **kwds
        )

    def parse_command(self, cmd: str, **kwds: Any) -> Any:
        """
        Parse a command without `#` prefix.
        """
        return self.parse(
            StringLexer(cmd, stat=1, encoding=self.__class__.__text_encoding__), **kwds
        )

    def parse_args(self, args_string: str) -> Tuple[tuple, Dict[str, Any]]:
        return Parser(
            StringLexer(
                args_string, stat=2, encoding=self.__class__.__text_encoding__), self
        ).parse_args()
