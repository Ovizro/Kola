from abc import ABCMeta
from typing import (Any, Callable, Dict, Iterable, Optional, Set, Tuple, Union,
                    overload)

from typing_extensions import Self

from .command import Command, CommandLike
from .mask import Mask, ClassTypeMask


class CommandSetMeta(ABCMeta):
    __command_field__: Set[CommandLike]
    __virtual_table__: Dict[str, str]

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any], **kwds: Any) -> Self: ...
    def generate_raw_commands(self) -> Dict[str, Any]: ...
    @overload
    def register_command(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_command(
        self, __name: Optional[str] = ..., *, alias: Union[Iterable[str], str] = ..., virtual: bool = False, **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_text(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_text(
        self, *, alias: Union[Iterable[str], str] = ..., virtual: bool = False, **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_number(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_number(
        self, *, alias: Union[Iterable[str], str] = ..., virtual: bool = False, **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_annotation(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_annotation(
        self, *, alias: Union[Iterable[str], str] = ..., virtual: bool = False, **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    

class CommandSet(metaclass=CommandSetMeta):
    __slots__ = ["raw_command_set", "_bound_command_cache"]

    raw_command_set: Dict[str, Callable]
    _bound_command_set: Dict[str, Callable]

    def __init__(self) -> None: ...
    def check_virtual(self, command: Command) -> bool: ...
    def get(self, __key: str, default: Optional[Callable] = ...) -> Optional[Callable]: ...
    @classmethod
    def mask(cls, type: Union["Mask.MType", str] = "") -> ClassTypeMask: ...
    def __kola_caller__(self, command: Command, args: tuple, kwargs: Dict[str, Any], **kwds) -> Any: ...
    def __getitem__(self, __key: str) -> Callable: ...
