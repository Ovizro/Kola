from types import MethodType
from typing_extensions import Literal
from typing import Any, Callable, Dict, Generator, Iterable, Mapping, NamedTuple, Optional, Set, Tuple, Type, Union, cast, overload

from .lexer import BaseLexer, StringLexer, FileLexer
from .parser import Parser
from .exception import KoiLangCommandError


class EnvNode(NamedTuple):
    name: str
    command_set: Union[Dict[str, Callable], "KoiLang"]
    next: Optional["EnvNode"] = None


class Command(object):
    __slots__ = ["__name__", "__func__", "method_type", "envs", "suppression", "alias"]

    def __init__(
            self, name: str,
            func: Callable,
            *,
            method: Literal["static", "class", "default"] = "default",
            envs: Union[Iterable[str], str] = tuple(),
            alias: Union[Iterable[str], str] = tuple(),
            suppression: bool = False
        ) -> None:
        self.__name__ = name
        self.__func__ = func
        self.method_type = method
        if envs and method != "default":
            raise KoiLangCommandError(
                "cannot accesss the environment for class method and static method"
            )
        self.envs = (envs,) if isinstance(envs, str) else tuple(envs)
        self.alias = (alias,) if isinstance(alias, str) else tuple(alias)
        self.suppression = suppression

    def bind(self, ins: Optional["KoiLang"], owner: Optional[Type["KoiLang"]] = None) -> Callable:
        """binding command function with an instance"""
        if self.method_type == "default" and ins is not None:
            return MethodType(self, ins)
        elif self.method_type == "class":
            return MethodType(self, owner or type(ins))
        else:
            return self
    
    def generate_commands(self, vmobj: "KoiLang", force: bool = False) -> Generator[Tuple[str, Callable], None, None]:
        if not self.suppression or force:
            bound_func = self.bind(vmobj)
            yield self.__name__, bound_func
            for i in self.alias:
                yield i, bound_func

    def __get__(self, instance: Any, owner: type) -> Callable:
        return self.bind(instance, cast(Type[KoiLang], owner))

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.method_type == "default" and self.envs:
            vmobj: KoiLang = args[0]
            env_name, _ = vmobj.top
            if env_name not in self.envs:
                raise KoiLangCommandError(f"unmatched environment {env_name}")
        return self.__func__(*args, **kwds)
    
    def __repr__(self) -> str:
        return f"<KoiLang command {self.__name__} with {self.__func__}>"


class BaseEnv(Command):
    __slots__ = ["env_name"]

    def __init__(
            self,
            name: str,
            func: Callable,
            *,
            method: Literal["static", "class", "default"] = "default",
            env_name: Optional[str] = None,
            **kwds
        ) -> None:
        super().__init__(name, func, method=method, **kwds)
        self.env_name = env_name or name

    def bind(self, ins: "KoiLang", owner: Optional[Type["KoiLang"]] = None) -> Callable:
        if ins is not None:
            return MethodType(self, ins)
        return self
    
    def __call__(self, vmobj: "KoiLang", *args, **kwds) -> Any:
        if self.method_type == "static":
            return super().__call__(*args, **kwds)
        elif self.method_type == "class":
            return super().__call__(type(vmobj), *args, **kwds)
        else:
            return super().__call__(vmobj, *args, **kwds)

    def __repr__(self) -> str:
        return f"<KoiLang command {self.__name__} with {self.__func__} on '{self.env_name}'>"


class EnvEnter(BaseEnv):
    __slots__ = ["command_set", "command_set_extra", "auto_pop"]

    def __init__(
            self,
            name: str,
            func: Callable,
            *,
            command_set: Union[Dict[str, Callable], "KoiLang", None] = None,
            auto_pop: bool = True,
            **kwds
        ) -> None:
        super().__init__(name, func, **kwds)
        self.command_set = command_set
        self.auto_pop = auto_pop
        self.command_set_extra: Set[Command] = set()
    
    def __call__(self, vmobj: "KoiLang", *args, **kwds) -> Any:
        if self.auto_pop and vmobj.top[0] == self.env_name:
            vmobj.pop()
        vmobj.push(self.env_name, self.command_set or {})
        for i in self.command_set_extra:
            vmobj.update(i.generate_commands(vmobj, True))
        return super().__call__(vmobj, *args, **kwds)

    @overload
    def exit_command(self, func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def exit_command(self, func: Optional[str] = None, *, method: Literal["static", "class", "default"] = ...,
                alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
    def exit_command(self, func: Union[Callable, str, None] = None, **kwds) -> Union[Callable[[Callable], Command], Command]:
        """
        Define a command to exit current environment
        """
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            if isinstance(func, str):
                name = func
            else:
                name = wrapped_func.__name__
            cmd = EnvExit(name, wrapped_func, env_name=self.env_name, suppression=True, **kwds)
            self.command_set_extra.add(cmd)
            self.auto_pop = False
            return cmd
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    
    @overload
    def env_command(self, func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def env_command(self, func: Optional[str] = None, *, method: Literal["static", "class", "default"] = ...,
                envs: Union[Iterable[str], str] = ..., alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
    def env_command(self, func: Union[Callable, str, None] = None, **kwds) -> Union[Callable[[Callable], Command], Command]:
        """
        Define a command only can be used in current environment
        """
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            if isinstance(func, str):
                name = func
            else:
                name = wrapped_func.__name__
            cmd = Command(name, wrapped_func, suppression=True, **kwds)
            self.command_set_extra.add(cmd)
            return cmd
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    
    @overload
    def env_text(self, func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def env_text(self, *, method: Literal["static", "class", "default"] = ...,
                envs: Union[Iterable[str], str] = ..., alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
    def env_text(self, func: Optional[Callable] = None, **kwds) -> Union[Callable[[Callable], Command], Command]:
        """
        Define a text command only can be used in current environment
        """
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            cmd = Command("@text", wrapped_func, suppression=True, **kwds)
            self.command_set_extra.add(cmd)
            return cmd
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    
    @overload
    def env_number(self, func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def env_number(self, *, method: Literal["static", "class", "default"] = ...,
                envs: Union[Iterable[str], str] = ..., alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
    def env_number(self, func: Optional[Callable] = None, **kwds) -> Union[Callable[[Callable], Command], Command]:
        """
        Define a number command only can be used in current environment
        """
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            cmd = Command("@number", wrapped_func, suppression=True, **kwds)
            self.command_set_extra.add(cmd)
            return cmd
        if callable(func):
            return wrapper(func)
        else:
            return wrapper


class EnvExit(BaseEnv):
    __slots__ = []

    def __init__(
            self,
            name: str,
            func: Callable,
            *,
            env_name: str,
            **kwds
        ) -> None:
        super().__init__(name, func, env_name=env_name, envs=env_name, **kwds)
    
    def __call__(self, vmobj: "KoiLang", *args: Any, **kwds: Any) -> Any:
        ret = super().__call__(vmobj, *args, **kwds)
        assert vmobj.pop()[0] == self.env_name
        return ret


class EnvClsEnter(BaseEnv):
    __slots__ = ["auto_pop", "command_set_class", "exit_entry"]

    def __init__(
            self, 
            name: str,
            func: Callable,
            *,
            command_set_class: Type["KoiLang"],
            env_name: Optional[str] = None,
            exit_entry: Union[str, Iterable[str]] = tuple(),
            **kwds
        ) -> None:
        super().__init__(name, func, env_name=env_name or command_set_class.__name__, **kwds)
        self.auto_pop = not exit_entry
        self.command_set_class = command_set_class
        if isinstance(exit_entry, str):
            self.exit_entry = (exit_entry,)
        else:
            self.exit_entry = tuple(exit_entry)

    def __call__(self, vmobj: "KoiLang", *args, **kwds) -> Any:
        if self.auto_pop and vmobj.top[0] == self.env_name:
            vmobj.pop()

        cmd_set = self.command_set_class(parent=vmobj)
        vmobj.push(self.env_name, cmd_set)
        for i in self.exit_entry:
            func: Callable = getattr(cmd_set, i)
            exit_cmd = EnvExit(func.__name__, func, env_name=self.env_name, method="static")
            vmobj.update(exit_cmd.generate_commands(vmobj))
        return super().__call__(cmd_set, *args, **kwds)


class KoiLangMeta(type):
    """
    Metaclass for KoiLang class
    """
    __command_field__: Set[Command]

    def __new__(cls, name: str, base: Tuple[type, ...], attr: Dict[str, Any]):
        __command_field__ = {
            i for i in attr.values() if isinstance(i, Command)
        }
        for i in base:
            if isinstance(i, KoiLangMeta):
                __command_field__.update(i.__command_field__)
        attr["__command_field__"] = __command_field__

        return super().__new__(cls, name, base, attr)
    
    @staticmethod
    def eval_commands(field: Set[Command], ins: Any) -> Dict[str, Callable]:
        cmd_set = {}
        for i in field:
            cmd_set.update(i.generate_commands(ins))
        return cmd_set

    def get_command_set(self, instance: Any) -> Dict[str, Callable]:
        return self.eval_commands(self.__command_field__, instance)

    @overload
    def register_command(self, func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_command(self, func: Optional[str] = None, *, method: Literal["static", "class", "default"] = ...,
                envs: Union[Iterable[str], str] = ..., alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
    def register_command(self, func: Union[Callable, str, None] = None, **kwds) -> Union[Callable[[Callable], Command], Command]:
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            if isinstance(func, str):
                name = func
            else:
                name = wrapped_func.__name__
            cmd = Command(name, wrapped_func, suppression=True, **kwds)
            self.__command_field__.add(cmd)
            return cmd
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    
    def __repr__(self) -> str:
        return f"<KoiLang command set '{self.__qualname__}'>"


class KoiLang(metaclass=KoiLangMeta):
    """
    Main class for KoiLang virtual machine.
    """
    __slots__ = ["_stack", "back"]

    back: Optional["KoiLang"]

    def __init__(self, parent: Optional["KoiLang"] = None) -> None:
        command_set = self.__class__.get_command_set(self)
        self._stack = EnvNode("__init__", command_set)
        self.back = parent
    
    def get_env(self, name: str) -> Union[Dict[str, Callable], "KoiLang"]:
        stack = self._stack
        while stack:
            if stack.name == name:
                return stack.command_set
            stack = stack.next
        raise KeyError(f"environment {name} not found")
    
    def get(self, key: str, default: Optional[Callable] = None) -> Optional[Callable]:
        return self.__get(key, default)
    
    def update(self, other: Union[Mapping[str, Callable], Iterable[Tuple[str, Callable]]], **kwds) -> None:
        self._stack.command_set.update(other, **kwds)
    
    def keys(self) -> Iterable[str]:
        stack = self._stack
        while stack:
            yield from stack.command_set.keys()
            stack = stack.next
    
    def values(self) -> Iterable[Callable]:
        stack = self._stack
        while stack:
            yield from stack.command_set.values()
            stack = stack.next
        
    def items(self) -> Iterable[Tuple[str, Callable]]:
        stack = self._stack
        while stack:
            yield from stack.command_set.items()
            stack = stack.next
    
    def push(self, name: str, commands: Union[Dict[str, Callable], "KoiLang", Set[Command]]) -> None:
        if isinstance(commands, set):
            commands = self.__class__.eval_commands(commands, self)
        elif isinstance(commands, KoiLang):
            commands.at_start()
        self._stack = EnvNode(name, commands, self._stack)
    
    def pop(self) -> Tuple[str, Union[Dict[str, Callable], "KoiLang"]]:
        if self._stack.next is None:
            raise KoiLangCommandError("cannot pop inital stack")
        top = self.top
        if isinstance(top[1], KoiLang):
            top[1].at_end()
        self._stack = self._stack.next
        return top
    
    def at_start(self) -> None:
        """
        Parser initalize method. Called before parsing start.
        """
    
    def at_end(self) -> None:
        """
        Parser finalize method. Called after parsing end.
        """

    def parse(self, lexer: Union[BaseLexer, str]) -> None:
        """
        Parse kola text or lexer from other method.
        """
        if isinstance(lexer, str):
            lexer = StringLexer(lexer)

        self.at_start()
        Parser(lexer, self).exec()
        self.at_end()

    def parse_file(self, path: str, **kwds) -> Any:
        return self.parse(FileLexer(path), **kwds)

    def parse_command(self, cmd: str, **kwds) -> Any:
        return self.parse(StringLexer(cmd, stat=1), **kwds)

    def parse_args(self, args: str) -> Tuple[tuple, Dict[str, Any]]:
        return Parser(StringLexer(args, stat=2), self).parse_args()
    
    def __get(self, key: str, default: Optional[Callable]) -> Optional[Callable]:
        # sourcery skip: use-named-expression
        stack = self._stack
        while stack:
            command = stack.command_set.get(key, None)
            if command:
                return command
            stack = stack.next
        return default

    @property
    def top(self) -> Tuple[str, Union[Dict[str, Callable], "KoiLang"]]:
        return self._stack[:2]
    
    @property
    def home(self) -> "KoiLang":
        cur = self
        while cur.back:
            cur = cur.back
        return cur
    
    def __getitem__(self, key: str) -> Callable:
        # sourcery skip: use-named-expression
        command = self.__get(key, None)
        if not command:
            raise KeyError(f"command '{key}' not found")
        return command
        
    def __contains__(self, key: str) -> bool:
        return self.__get(key, None) is not None

    def __len__(self) -> int:
        length = 0
        stack = self._stack
        while stack:
            length += 1
            stack = stack.next
        return length

    def __repr__(self) -> str:
        return f"<KoiLang {self.__class__.__qualname__} object in environment {self.top[0]}>"


@overload
def kola_command(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_command(func: Optional[str] = None, *, method: Literal["static", "class", "default"] = ...,
                envs: Union[Iterable[str], str] = ..., alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
def kola_command(func: Union[Callable[..., Any], str, None] = None,
                **kwds) -> Union[Command, Callable[[Callable], Command]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> Command:
        if isinstance(func, str):
            name = func
        else:
            name = wrapped_func.__name__
        return Command(name, wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_text(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_text(*, method: Literal["static", "class", "default"] = ..., envs: Union[Iterable[str], str] = ...,
            alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
def kola_text(func: Optional[Callable[..., Any]] = None, **kwds) -> Union[Command, Callable[[Callable], Command]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> Command:
        return Command("@text", wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_number(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_number(*, method: Literal["static", "class", "default"] = ..., envs: Union[Iterable[str], str] = ...,
            alias: Union[Iterable[str], str] = ...) -> Callable[[Callable[..., Any]], Command]: ...
def kola_number(func: Optional[Callable[..., Any]] = None, **kwds) -> Union[Command, Callable[[Callable], Command]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> Command:
        return Command("@number", wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_env(func: Callable[..., Any], **kwds) -> EnvEnter: ...
@overload
def kola_env(func: Optional[str] = None, *, env_name: str = ..., method: Literal["static", "class", "default"] = ..., alias: Union[Iterable[str], str] = ...,
            envs: Union[Iterable[str], str] = ..., command_set: Union[Dict[str, Callable], "KoiLang"] = ...) -> Callable[[Callable[..., Any]], EnvEnter]: ...
def kola_env(func: Union[Callable[..., Any], str, None] = None, 
            *, env_name: Optional[str] = None, **kwds) -> Union[EnvEnter, Callable[[Callable], EnvEnter]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> EnvEnter:
        if isinstance(func, str):
            name = func
        else:
            name = wrapped_func.__name__
        return EnvEnter(name, wrapped_func, env_name=env_name, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_env_class(kola_cls: Type[KoiLang], **kwds) -> EnvClsEnter: ...
@overload
def kola_env_class(kola_cls: Optional[str] = None, *, enter: str = ..., alias: Union[Iterable[str], str] = ...,
                exit: Union[str, Iterable[str], None] = ..., envs: Union[str, Tuple[str,...]]) -> Callable[[Type[KoiLang]], EnvClsEnter]: ...
def kola_env_class(kola_cls: Union[Type[KoiLang], str, None] = None, *, enter: str = "enter", 
                exit: Union[str, Iterable[str], None] = None, **kwds) -> Union[Callable[[Type[KoiLang]], EnvClsEnter], EnvClsEnter]:
    def wrapper(wrapped_class: Type[KoiLang]) -> EnvClsEnter:
        if isinstance(kola_cls, str):
            env_name = kola_cls
        else:
            env_name = wrapped_class.__name__
        
        enter_func: Callable = getattr(wrapped_class, enter)
        if isinstance(enter_func, Command):
            enter_func.suppression = True
        enter_cmd = EnvClsEnter(
            enter_func.__name__,
            enter_func,
            env_name=env_name,
            command_set_class=wrapped_class,
            exit_entry=exit or (),
            **kwds
        )
        return enter_cmd
    if isinstance(kola_cls, type):
        return wrapper(kola_cls)
    else:
        return wrapper
