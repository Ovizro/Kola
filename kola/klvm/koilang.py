import os
import sys
from contextlib import contextmanager, suppress
from functools import partial
from threading import Lock
from types import TracebackType, new_class
from typing import (Any, Callable, Dict, Generator, List, Optional, Tuple,
                    Type, TypeVar, Union, overload)
from typing_extensions import Literal, Self

from ..exception import KoiLangError
from ..lexer import BaseLexer, FileLexer, StringLexer
from ..parser import Parser
from .command import Command
from .commandset import CommandSet, CommandSetMeta
from .environment import Environment


_T_EnvCls = TypeVar("_T_EnvCls", bound=Type[Environment])
_T_Handler = TypeVar("_T_Handler", bound=Type["AbstractHandler"])


class KoiLangMeta(CommandSetMeta):
    """
    metaclass for KoiLang class

    Provide encoding and command threshold support.
    """
    __text_encoding__: str
    __text_lstrip__: bool
    __command_threshold__: int
    __command_handlers__: List[Type["AbstractHandler"]]

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attr: Dict[str, Any],
        command_threshold: int = 0,
        encoding: Optional[str] = None,
        lstrip_text: Optional[bool] = None,
        **kwds: Any
    ) -> Self:
        """
        create a top-level language class

        :param name: class name
        :type name: str
        :param bases: class bases
        :type bases: Tuple[type, ...]
        :param attr: class namespace
        :type attr: Dict[str, Any]
        :param command_threshold: the `#` prefix length of commands, defaults to 0
        :type command_threshold: int, optional
        :param encoding: encoding for file parsing, defaults to None
        :type encoding: Optional[str], optional
        :param lstrip_text: whether to remove text indentation, defaults to True
        :type lstrip_text: bool, optional
        :return: new class
        :rtype: KoiLangMeta
        """
        # if not base KoiLang class, set a default value
        if not any(isinstance(i, cls) for i in bases):
            command_threshold = command_threshold or 1
            encoding = encoding or "utf-8"
            lstrip_text = lstrip_text if lstrip_text is not None else True
            if "__command_handlers__" not in attr:
                attr["__command_handlers__"] = []
        
        if command_threshold:
            assert command_threshold >= 0
            attr["__command_threshold__"] = command_threshold
        if lstrip_text is not None:
            attr["__text_lstrip__"] = lstrip_text
        if encoding:
            attr["__text_encoding__"] = encoding
        return super().__new__(cls, name, bases, attr, **kwds)

    def register_environment(self, env_class: _T_EnvCls) -> _T_EnvCls:
        self.__command_field__.add(env_class)
        return env_class
    
    def register_handler(self, handler: _T_Handler) -> _T_Handler:
        if "__command_handlers__" not in self.__dict__:
            # copy the handler list to avoid changing the base classes
            self.__command_handlers__ = self.__command_handlers__.copy()
        self.__command_handlers__.append(handler)
        return handler
    
    @property
    def writer(self) -> Type:
        """writer class for KoiLang file building

        :return: the writer class, which is a subclass of KoiLangWriter and current KoiLang class
        :rtype: Type[KoiLang, Self]
        """
        cache = None
        with suppress(AttributeError):
            cache = self.__writer_class
        if cache is not None:
            return cache
        cache = new_class(f"{self.__qualname__}.writer", (KoiLangWriter, self))
        self.__writer_class = cache
        return cache


class KoiLang(CommandSet, metaclass=KoiLangMeta):
    """
    main class for KoiLang virtual machine

    `KoiLang` class is the top-level interface of 'kola' package.
    Just create a subclass to define your own markup language based on KoiLang.
    """
    __slots__ = ["_handler", "_lock", "__top", "__exec_level"]

    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()
        self.__top = self
        self.__exec_level = 0
        self._handler = build_handlers(self.__class__.__command_handlers__, self)
    
    def push_prepare(self, __env_type: Type[Environment]) -> Environment:
        env = __env_type(self.__top)
        env.set_up(self.__top)
        return env

    def push_apply(self, __env_cache: Environment) -> None:
        assert __env_cache.back is self.__top
        with self._lock:
            self.__top = __env_cache
    
    def pop_prepare(self, __env_type: Optional[Type[Environment]] = None) -> Environment:
        top = self.__top
        if top is self:  # pragma: no cover
            raise ValueError('cannot pop the inital environment')
        if __env_type is None:
            assert isinstance(top, Environment)
        else:
            while isinstance(top, Environment) and top.__class__.__env_autopop__:
                if isinstance(top, __env_type):
                    break
                top = top.back
            else:
                if not isinstance(top, __env_type):  # pragma: no cover
                    raise ValueError("unmatched environment")
        return top

    def pop_apply(self, __env_cache: Environment) -> None:
        with self._lock:
            top = self.__top
            self.__top = __env_cache.back
        while isinstance(top, Environment):
            top.tear_down(self.__top)
            if top is __env_cache:
                break
            top = top.back
        else:
            raise ValueError('cannot pop the inital environment')
    
    def add_handler(self, handler: Union[Type["AbstractHandler"], "AbstractHandler"]) -> "AbstractHandler":
        if isinstance(handler, type):
            handler = handler(self)
        self._handler = self._handler.insert(handler)
        return handler
    
    def remove_handler(self, handler: "AbstractHandler") -> None:
        hdl = self._handler.remove(handler)
        if hdl is None:  # pragma: no cover
            raise ValueError("cannot remove all handlers")
        self._handler = hdl

    def __parse(self, __lexer: BaseLexer, *, close_lexer: bool = True) -> None:
        parser = Parser(__lexer, self)
        try:
            with self.exec_block():
                while True:
                    try:
                        # Parser.exec() is a fast C level loop
                        parser.exec()
                    except KoiLangError:
                        if not self.on_exception(*sys.exc_info()):
                            raise
                    else:
                        break
        finally:
            if close_lexer:
                __lexer.close()
    
    def __parse_and_ret(self, __lexer: BaseLexer, *, close_lexer: bool = True) -> Generator[Any, None, None]:
        parser = Parser(__lexer, self)
        try:
            with self.exec_block():
                while True:
                    try:
                        yield from parser
                    except KoiLangError:
                        if not self.on_exception(*sys.exc_info()):
                            raise
                    else:
                        break
        finally:
            if close_lexer:
                __lexer.close()

    @overload
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: Literal[False] = False, close_lexer: bool = True) -> None: ...
    @overload  # noqa: E301
    def parse(
        self,
        lexer: Union[BaseLexer, str],
        *,
        with_ret: Literal[True],
        close_lexer: bool = True
    ) -> Generator[Any, None, None]: ...
    
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: bool = False, close_lexer: bool = True) -> Any:
        """parse kola text

        :param lexer: Lexer object or legal KoiLang string
        :type lexer: Union[BaseLexer, str]
        :param with_ret: if true, return a gererater where command returns would be yielded, defaults to False
        :type with_ret: bool, optional
        :param close_lexer: whether or not to close the lexer, defaults to True
        :type close_lexer: bool, optional
        :raises ValueError: when a KoiLang string given without trying to close it
        :return: return a generator if `with_ret` set
        :rtype: Generator[Any, None, None] or None
        """
        if isinstance(lexer, str):
            if not close_lexer:  # pragma: no cover
                raise ValueError("inner string lexer must be closed at the end of parsing")
            lexer = StringLexer(
                lexer,
                encoding=self.__class__.__text_encoding__,
                command_threshold=self.__class__.__command_threshold__,
                no_lstrip=not self.__class__.__text_lstrip__
            )
        if with_ret:
            return self.__parse_and_ret(lexer, close_lexer=close_lexer)
        else:
            self.__parse(lexer, close_lexer=close_lexer)
        
    def parse_file(self, path: Union[str, bytes, os.PathLike], *, encoding: Optional[str] = None, **kwds: Any) -> Any:
        """
        parse a kola file.
        """
        return self.parse(
            FileLexer(
                path, encoding=encoding or self.__class__.__text_encoding__,
                command_threshold=self.__class__.__command_threshold__,
                no_lstrip=not self.__class__.__text_lstrip__
            ), **kwds
        )
    
    @contextmanager
    def exec_block(self) -> Generator[Self, None, None]:
        if not self.__exec_level:
            self.at_start()
        with self._lock:
            self.__exec_level += 1
        try:
            yield self
        finally:
            with self._lock:
                self.__exec_level -= 1
            if not self.__exec_level:
                self.at_end()

    def __getitem__(self, __key: str) -> Callable:
        if self.__top is self:
            return super().__getitem__(__key)
        return self.__top[__key]

    def __kola_caller__(self, command: Command, args: tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        return self._handler(command, args, kwargs, **kwds)

    @property
    def top(self) -> CommandSet:
        return self.__top
    
    @property
    def home(self) -> Self:
        return self

    @partial(Command, "@start", virtual=True)
    def at_start(self) -> None:
        """
        parser initalize command
        
        It is called before parsing start.
        """

    @partial(Command, "@end", virtual=True)
    def at_end(self) -> None:
        """
        parser finalize command
        
        It is called after parsing end. And the return value
        will be that of 'parse' method.
        """
    
    @partial(Command, "@exception", virtual=True)
    def on_exception(self, exc_type: Type[KoiLangError], exc_ins: Optional[KoiLangError], traceback: TracebackType) -> None:
        """
        exception handling command

        It is called when a KoiLang error occurs.
        If the command wishes to suppress the exception, it should a true value.
        """


from .handler import AbstractHandler, build_handlers
from .writer import KoiLangWriter
