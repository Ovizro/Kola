from abc import ABCMeta
from types import MethodType
from typing import Any, Callable, Dict, Optional, Set, Tuple, Type, Union
from typing_extensions import Self

from .command import CommandLike, Command


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

    def generate_raw_commands(self) -> Dict[str, Any]:
        cmd_set = {}
        for cls in reversed(self.__mro__):
            cls: Type
            if not isinstance(cls, CommandSetMeta):
                continue
            for c in cls.__command_field__:
                cmd_set.update(c.__kola_command__())
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
    
    def __repr__(self) -> str:
        return f"<kola command set '{self.__qualname__}'>"


class CommandSet(object, metaclass=CommandSetMeta):
    __slots__ = ["raw_command_set", "_bound_command_cache"]

    def __init__(self) -> None:
        super().__init__()
        self.raw_command_set = self.__class__.generate_raw_commands()
        self._bound_command_cache = {}

    def get(self, __key: str, default: Optional[Callable] = None) -> Optional[Callable]:
        """
        get command in the command set

        NOTICE: This method will only try to get its own commands.
        If you want to get a command as a normal case, use `__getitem__` instead.
        """
        cache = self._bound_command_cache.get(__key, None)
        if cache is not None:
            return cache
        raw_cmd = self.raw_command_set.get(__key, default)
        if raw_cmd is default:
            return raw_cmd
        
        assert raw_cmd
        bound_cmd = MethodType(raw_cmd, self)
        self._bound_command_cache[__key] = bound_cmd
        return bound_cmd

    def __kola_caller__(self, command: Command, args: tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        return command.__func__(self, *args, **kwargs)

    def __getitem__(self, __key: str) -> Callable:
        cmd = self.get(__key)
        if cmd is None:
            raise KeyError(f"unknown command '{__key}'")
        return cmd
    
    def __repr__(self) -> str:
        return f"<kola {self.__class__.__name__} object at 0x{id(self):08X}>"
