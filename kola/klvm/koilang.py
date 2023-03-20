from contextlib import contextmanager
import os
import sys
from threading import Lock
from types import TracebackType, new_class
from typing import Any, Callable, ClassVar, Dict, Generator, Optional, Tuple, Type, TypeVar, Union, overload
from typing_extensions import Literal, Self

from ..lexer import BaseLexer, FileLexer, StringLexer
from ..parser import Parser
from ..exception import KoiLangError
from .command import Command
from .commandset import CommandSetMeta, CommandSet
from .environment import Environment


_T_EnvCls = TypeVar("_T_EnvCls", bound=Type[Environment])


class KoiLangMeta(CommandSetMeta):
    """
    metaclass for KoiLang class

    Provide encoding and command threshold support.
    """
    __text_encoding__: str
    __command_threshold__: int

    builtin_mapping: ClassVar[Dict[str, str]] = {
        "at_start": "@start", "at_end": "@end", "on_exception": "@exception"
    }

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any],
                command_threshold: int = 0, encoding: Optional[str] = None, **kwds: Any):
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
        :return: new class
        :rtype: KoiLangMeta
        """
        has_base = any(isinstance(i, cls) for i in bases)
        if command_threshold or not has_base:
            assert command_threshold >= 0
            attr["__command_threshold__"] = command_threshold or 1
        if encoding or not has_base:
            attr["__text_encoding__"] = encoding or "utf-8"
        for k, n in cls.builtin_mapping.items():
            if k not in attr:
                continue
            cmd = attr[k]
            if not isinstance(cmd, Command):
                attr[k] = Command(n, cmd)
        return super().__new__(cls, name, bases, attr, **kwds)

    def register_environment(self, env_class: _T_EnvCls) -> _T_EnvCls:
        self.__command_field__.add(env_class)
        return env_class
    
    @property
    def writer(self) -> Type:
        cache = getattr(self, "__writer_class__", None)
        if cache is not None:
            return cache
        cache = new_class(f"{self.__qualname__}.writer", (KoiLangWriter, self))
        self.__writer_class__ = cache
        return cache


class KoiLang(CommandSet, metaclass=KoiLangMeta):
    """
    main class for KoiLang virtual machine

    `KoiLang` class is the top-level interface of 'kola' package.
    Just create a subclass to define your own markup language based on KoiLang.
    """
    __slots__ = ["_lock", "__top", "__exec_level"]

    def __init__(self) -> None:
        super().__init__()
        self._lock = Lock()
        self.__top = self
        self.__exec_level = 0
    
    def push_start(self, __env_type: Type[Environment]) -> Environment:
        env = __env_type(self.__top)
        env.at_initialize(self.__top)
        return env

    def push_end(self, __env_cache: Environment) -> None:
        assert __env_cache.back is self.__top
        with self._lock:
            self.__top = __env_cache
    
    def pop_start(self, __env_type: Optional[Type[Environment]] = None) -> Environment:
        top = self.__top
        if top is self:
            raise ValueError('cannot pop the inital environment')
        if __env_type is None:
            assert isinstance(top, Environment)
        else:
            while isinstance(top, Environment) and top.__class__.__env_autopop__:
                if isinstance(top, __env_type):
                    break
                top = top.back
            else:
                if not isinstance(top, __env_type):
                    raise ValueError("unmatched environment")
        return top

    def pop_end(self, __env_cache: Environment) -> None:
        with self._lock:
            top = self.__top
            self.__top = __env_cache.back
        while isinstance(top, Environment):
            top.at_finalize(self.__top)
            if top is __env_cache:
                break
            top = top.back
        else:
            raise ValueError('cannot pop the inital environment')
    
    def ensure_env(self, names: Tuple[str, ...]) -> None:
        if isinstance(names, str):
            names = (names,)

        ng, pt = [], []
        for i in names:
            if i.startswith('!'):
                ng.append(i[1:])
            else:
                pt.append(i)

        reachable = []
        top = self.top
        while isinstance(top, Environment):
            reachable.append(top.__class__.__name__)
            if not top.__class__.__env_autopop__:
                break
            top = top.back
        else:
            # the base KoiLang object name is '__init__'
            reachable.append("__init__")

        if ((not ng or all(not self._ensure_env(reachable, i) for i in ng)) and
                (not pt or any(self._ensure_env(reachable, i) for i in pt))):
            return
        raise ValueError(f"unmatched environment name {reachable[0]}")
    
    @staticmethod
    def _ensure_env(reachable: list, name: str) -> bool:
        if name.startswith('+'):
            strict = True
            name = name[1:]
        else:
            strict = False
        if name.startswith('!'):
            inverse = True
            name = name[1:]
        else:
            inverse = False

        if strict:
            is_in = reachable[0] == name
        else:
            is_in = name in reachable
        return not is_in if inverse else is_in

        # for n in names:
        #     if n.startswith('+!'):
        #         while n[2:] in reachable:
        #             if len(reachable) < 2:
        #                 break
        #             cache = self.pop_start()
        #             self.pop_end(cache)
        #             reachable.popleft()
        #         else:
        #             continue
        #     elif n.startswith('!'):
        #         if any(i != n[1:] for i in reachable):
        #             continue
        #     elif n.startswith('+'):
        #         while reachable[0] != n[1:]:
        #             if len(reachable) < 2:
        #                 break
        #             cache = self.pop_start()
        #             self.pop_end(cache)
        #             reachable.popleft()
        #         else:
        #             continue
        #     elif n in reachable:
        #         continue
        #     raise ValueError(f"unmatched environment name {n}")
    
    def __parse(self, __lexer: BaseLexer) -> None:
        parser = Parser(__lexer, self)
        with self.exec_block():
            while True:
                try:
                    # Parser.exec() is a fast C level loop.
                    parser.exec()
                except KoiLangError:
                    if not self["@exception"](*sys.exc_info()):
                        raise
                else:
                    break
    
    def __parse_and_ret(self, __lexer: BaseLexer) -> Generator[Any, None, None]:
        parser = Parser(__lexer, self)
        with self.exec_block():
            while True:
                try:
                    yield from parser
                except KoiLangError:
                    if not self["@exception"](*sys.exc_info()):
                        raise
                else:
                    break

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
                args_string, stat=2, encoding=self.__class__.__text_encoding__
            ), self
        ).parse_args()
    
    @contextmanager
    def exec_block(self) -> Generator[Self, None, Optional[bool]]:
        if not self.__exec_level:
            self["@start"]()
        self.__exec_level += 1
        try:
            yield self
        finally:
            self.__exec_level -= 1
            if not self.__exec_level:
                self["@end"]()

    def __getitem__(self, __key: str) -> Callable:
        if self.__top is self:
            return super().__getitem__(__key)
        return self.__top[__key]

    def __kola_caller__(
        self,
        command: Command,
        args: tuple,
        kwargs: Dict[str, Any],
        *,
        bound_instance: Optional[CommandSet] = None,
        envs: Tuple[str, ...] = (),
        **kwds: Any
    ) -> Any:
        if envs:
            self.ensure_env(envs)
        return command.__func__(bound_instance or self, *args, **kwargs)

    @property
    def top(self) -> CommandSet:
        return self.__top
    
    @property
    def home(self) -> Self:
        return self

    def at_start(self) -> None:
        """
        parser initalize command
        
        It is called before parsing start.
        """

    def at_end(self) -> None:
        """
        parser finalize command
        
        It is called after parsing end. And the return value
        will be that of 'parse' method.
        """
        while isinstance(self.__top, Environment) and self.__top.__class__.__env_autopop__:
            cache = self.pop_start()
            self.pop_end(cache)
    
    def on_exception(self, exc_type: Type[KoiLangError], exc_ins: KoiLangError, traceback: TracebackType) -> None:
        """
        exception handling command

        It is called when a KoiLang error occurs.
        If the command wishes to suppress the exception, it should a true value.
        """


from .writer import KoiLangWriter
