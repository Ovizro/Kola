from abc import ABCMeta
from types import MethodType
from typing import Any, Callable, Dict, Generator, Iterable, Optional, Set, Tuple, Type, Union
from typing_extensions import Literal, Protocol, Self, runtime_checkable

from ..writer import BaseWriter


@runtime_checkable
class CommandLike(Protocol):
    def __kola_command__(
        self, __cmd_set: "CommandSet"
    ) -> Generator[Tuple[str, Callable], None, None]: ...


class Command(object):
    __slots__ = ["__name__", "__func__", "method_type", "suppression", "alias", "writer_func"]

    def __init__(
        self,
        __name: str,
        func: Callable,
        *,
        method: Literal["static", "class", "default"] = "default",
        alias: Union[Iterable[str], str] = tuple(),
        suppression: bool = False
    ) -> None:
        self.__name__ = __name
        self.__func__ = func
        self.method_type = method
        self.alias = (alias,) if isinstance(alias, str) else tuple(alias)
        self.suppression = suppression
        if self.__name__ == "@text":
            self.writer_func = BaseWriter.write_text
        else:
            self.writer_func = lambda writer, *args, **kwds: \
                writer.write_command(__name, *args, **kwds)

    def bind(self, ins: Optional["CommandSet"], owner: Optional[Type["CommandSet"]] = None) -> Callable:
        """binding command function with an instance"""
        return MethodType(self, ins)

    __get__ = bind

    def writer(self, func: Callable) -> Self:
        self.writer_func = func
        return self

    def __kola_command__(self, cmd_set: "CommandSet", force: bool = False) -> Generator:
        if not self.suppression or force:
            bound_func = self.bind(cmd_set)
            yield self.__name__, bound_func
            for i in self.alias:
                yield i, bound_func

    def __call__(self, vmobj: "CommandSet", *args: Any, **kwds: Any) -> Any:
        if self.method_type == "default":
            args = (vmobj,) + args
        elif self.method_type == "class":
            args = (vmobj.__class__,) + args
        return self.__func__(*args, **kwds)

    def __repr__(self) -> str:
        return f"<kola command {self.__name__} with {self.__func__}>"


class CommandSetMeta(ABCMeta):
    """
    metaclass for all command sets
    """
    __command_field__: Set[CommandLike]

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any], **kwds: Any) -> Self:
        command_field = {
            i for i in attr.values() if isinstance(i, (Command, CommandLike))
        }
        attr["__command_field__"] = command_field
        return super().__new__(cls, name, bases, attr, **kwds)

    def get_command_set(self, instance: Any) -> Dict[str, Callable]:
        cmd_set = {}
        for cls in reversed(self.mro()):
            cls: Type
            if not isinstance(cls, CommandSetMeta):
                continue
            for i in cls.__command_field__:
                cmd_set.update(i.__kola_command__(instance))
        return cmd_set

    def _command_register_factory(cmd_name: Optional[str] = None):  # type: ignore
        def inner(
            self,
            __func_or_name: Union[Callable, str, None] = None,
            **kwds
        ) -> Union[Callable[[Callable], Command], Command]:
            def wrapper(wrapped_func: Callable[..., Any]) -> Command:
                if cmd_name is not None:
                    assert not isinstance(__func_or_name, str)
                    name = cmd_name
                elif isinstance(__func_or_name, str):
                    name = __func_or_name
                else:
                    name = wrapped_func.__name__
                cmd = Command(name, wrapped_func, **kwds)
                self.__command_field__.add(cmd)
                return cmd
            if callable(__func_or_name):
                return wrapper(__func_or_name)
            else:
                return wrapper
        return inner

    register_command = _command_register_factory()
    register_text = _command_register_factory("@text")
    register_number = _command_register_factory("@number")
    register_annotation = _command_register_factory("@annotation")

    del _command_register_factory


class CommandSet(object, metaclass=CommandSetMeta):
    __slots__ = ["command_set"]

    def __init__(self) -> None:
        super().__init__()
        self.command_set = self.__class__.get_command_set(self)

    def get(self, __key: str, default: Optional[Callable] = None) -> Optional[Callable]:
        """
        get command in the command set

        NOTICE: This method will only try to get its own command.
        If you want to get a command as normal case, use `__getitem__` instead.
        """
        return self.command_set.get(__key, default)

    def __getitem__(self, __key: str) -> Callable:
        cmd = self.get(__key)
        if cmd is None:
            raise KeyError(f"unknown command '{__key}'")
        return cmd
