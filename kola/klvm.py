from typing import Any, Callable, Dict, NamedTuple, Optional, Set, Tuple, Union, overload
from typing_extensions import Literal
from types import MethodType

from .lexer import BaseLexer, StringLexer, FileLexer
from .parser import Parser
from .exception import KoiLangCommandError


class EnvNode(NamedTuple):
    name: str
    command_set: Union[Dict[str, Callable], "KoiLang"]
    next: Optional["EnvNode"] = None


class KoiLangCommand(object):
    __slots__ = ["__name__", "__func__", "method_type", "envs"]

    def __init__(
            self, name: str,
            func: Callable,
            *,
            method: Literal["static", "class", "default"] = "default",
            envs: Union[Tuple[str], str] = tuple()
        ) -> None:
        self.__name__ = name
        self.__func__ = func
        self.method_type = method
        if envs and method != "default":
            raise KoiLangCommandError(
                "cannot accesss the environment for class method and static method"
            )
        if isinstance(envs, str):
            envs = (envs,)
        self.envs = envs

    def bind(self, ins: "KoiLang") -> Callable:
        """binding command function with an instance"""
        if self.method_type == "default":
            return MethodType(self, ins)
        elif self.method_type == "class":
            return MethodType(self, type(ins))
        else:
            return self

    def __get__(self, instance: Any, owner: type) -> Callable:
        if instance is not None:
            return self.bind(instance)
        else:
            return self

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self.method_type == "default" and self.envs:
            vmobj: KoiLang = args[0]
            env_name, _ = vmobj.top
            if env_name not in self.envs:
                raise KoiLangCommandError(f"unmatched environment {env_name}")
        return self.__func__(*args, **kwds)


class KoiLangEnvironment(KoiLangCommand):
    __slots__ = ["env_name", "command_set", "exit_func"]

    def __init__(
            self,
            name: str,
            func: Callable,
            *,
            env_name: Optional[str] = None,
            envs: Union[Tuple[str], str] = tuple(),
            command_set: Union[Dict[str, Callable], "KoiLang", None] = None
        ) -> None:
        super().__init__(name, func, envs=envs)
        self.env_name = env_name or name
        self.command_set = command_set
    
    def at_exit(self, exit_func: Callable) -> "KoiLangEnvironmentExit":
        exit_func = KoiLangEnvironmentExit(exit_func.__name__, exit_func, env_name=self.env_name)
        self.exit_func = exit_func
        return exit_func
    
    def __call__(self, vmobj: "KoiLang", *args: Any, **kwds: Any) -> Any:
        if self.exit_func is None and vmobj.top[0] == self.env_name:
            vmobj.pop()
        vmobj.push(self.env_name, self.command_set)
        return super().__call__(vmobj, *args, **kwds)


class KoiLangEnvironmentExit(KoiLangCommand):
    __slots__ = ["env_name"]

    def __init__(
            self,
            name: str,
            func: Callable,
            *,
            env_name: str,
        ) -> None:
        super().__init__(name, func, envs=env_name)
        self.env_name = env_name
    
    def __call__(self, vmobj: "KoiLang", *args: Any, **kwds: Any) -> Any:
        ret = super().__call__(vmobj, *args, **kwds)
        vmobj.pop()
        return ret

class KoiLangMeta(type):
    """
    Metaclass for KoiLang class
    """
    __command_field__: Set[KoiLangCommand]

    def __new__(cls, name: str, base: Tuple[type, ...], attr: Dict[str, Any]):
        __command_field__ = {
            i for i in attr.values() if isinstance(i, KoiLangCommand)
        }
        for i in base:
            if isinstance(i, KoiLangMeta):
                __command_field__.update(i.__command_field__)
        attr["__command_field__"] = __command_field__

        return super().__new__(cls, name, base, attr)

    def get_command_set(self, instance: Any) -> Dict[str, Callable]:
        return {i.__name__: i.bind(instance) for i in self.__command_field__}

    def register_command(self, func: Callable, *, target: Optional[str] = None) -> None:
        if not isinstance(func, KoiLangCommand):
            func = KoiLangCommand(target or func.__name__, func)
        self.__command_field__.add(func)


class KoiLang(metaclass=KoiLangMeta):
    """
    Main class for KoiLang virtual machine.
    """
    __slots__ = ["_stack"]

    def __init__(self) -> None:
        command_set = self.__class__.get_command_set(self)
        self._stack = EnvNode("__init__", command_set)

    def __getitem__(self, key: str) -> Callable:
        # sourcery skip: use-named-expression
        command = _klvm_get(self, key, None)
        if not command:
            raise KeyError(f"command '{key}' not found")
        return command
    
    def __len__(self) -> int:
        length = 0
        stack = self._stack
        while stack:
            length += 1
            stack = stack.next
        return length
    
    def get_env(self, name: str) -> Union[Dict[str, Callable], "KoiLang"]:
        stack = self._stack
        while stack:
            if stack.name == name:
                return stack.command_set
            stack = stack.next
        raise KeyError(f"environment {name} not found")
    
    def get(self, key: str, default: Optional[Callable] = None) -> Optional[Callable]:
        return _klvm_get(self, key, default)
    
    @property
    def top(self) -> Tuple[str, Union[Dict[str, Callable], "KoiLang"]]:
        return self._stack[:2]
    
    def push(self, name: str, commands: Union[Dict[str, Callable], "KoiLang", None] = None) -> None:
        commands = commands or {}
        self._stack = EnvNode(name, commands, self._stack)
    
    def pop(self) -> Tuple[str, Union[Dict[str, Callable], "KoiLang"]]:
        if self._stack.next is None:
            raise KoiLangCommandError("cannot pop inital stack")
        top = self.top
        self._stack = self._stack.next
        return top

    def parse(self, lexer: Union[BaseLexer, str]) -> None:
        if isinstance(lexer, str):
            lexer = StringLexer(lexer)
        Parser(lexer, self).exec()

    def parse_file(self, path: str) -> Any:
        return self.parse(FileLexer(path))

    def parse_command(self, cmd: str) -> Any:
        return self.parse(StringLexer(cmd, stat=1))

    def parse_args(self, args: str) -> Tuple[tuple, Dict[str, Any]]:
        return Parser(StringLexer(args, stat=2), self).parse_args()


def _klvm_get(vmobj: KoiLang, key: str, default: Optional[Callable]) -> Optional[Callable]:
    # sourcery skip: use-named-expression
    stack = vmobj._stack
    while stack:
        command = stack.command_set.get(key, None)
        if command:
            return command
        stack = stack.next
    return default


@overload
def kola_command(func: Optional[str] = None, *, method: Literal["static", "class", "default"] = ..., envs: Union[Tuple[str], str] = ...) -> Callable[[Callable[..., Any]], KoiLangCommand]: ...
@overload
def kola_command(func: Callable[..., Any]) -> KoiLangCommand: ...
def kola_command(func: Union[Callable[..., Any], str, None] = None, **kwds) -> Union[KoiLangCommand, Callable[[Callable], KoiLangCommand]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> KoiLangCommand:
        if isinstance(func, str):
            name = func
        else:
            name = wrapped_func.__name__
        return KoiLangCommand(name, wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_env(func: Optional[str] = None, *, cmd_name: str = ..., envs: Union[Tuple[str], str] = ...) -> Callable[[Callable[..., Any]], KoiLangEnvironment]: ...
@overload
def kola_env(func: Callable[..., Any]) -> KoiLangEnvironment: ...
def kola_env(func: Union[Callable[..., Any], str, None] = None, *, cmd_name: Optional[str] = None, **kwds) -> Union[KoiLangEnvironment, Callable[[Callable], KoiLangEnvironment]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> KoiLangEnvironment:
        if isinstance(func, str):
            env_name = func
        else:
            env_name = wrapped_func.__name__
        return KoiLangEnvironment(cmd_name or wrapped_func.__name__, wrapped_func, env_name=env_name, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_text(*, method: Literal["static", "class", "default"] = ..., envs: Union[Tuple[str], str] = ...) -> Callable[[Callable[..., Any]], KoiLangCommand]: ...
@overload
def kola_text(func: Callable[..., Any]) -> KoiLangCommand: ...
def kola_text(func: Optional[Callable[..., Any]] = None, **kwds) -> Union[KoiLangCommand, Callable[[Callable], KoiLangCommand]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> KoiLangCommand:
        return KoiLangCommand("@text", wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper


@overload
def kola_number(*, method: Literal["static", "class", "default"] = ..., envs: Union[Tuple[str], str] = ...) -> Callable[[Callable[..., Any]], KoiLangCommand]: ...
@overload
def kola_number(func: Callable[..., Any]) -> KoiLangCommand: ...
def kola_number(func: Optional[Callable[..., Any]] = None, **kwds) -> Union[KoiLangCommand, Callable[[Callable], KoiLangCommand]]:
    def wrapper(wrapped_func: Callable[..., Any]) -> KoiLangCommand:
        return KoiLangCommand("@number", wrapped_func, **kwds)
    if callable(func):
        return wrapper(func)
    else:
        return wrapper
