from abc import ABCMeta
from typing import (Any, Callable, Dict, Iterable, Optional, Set, Tuple, Union,
                    overload)

from typing_extensions import Self

from .command import Command, CommandLike


class CommandSetMeta(ABCMeta):
    __command_field__: Set[CommandLike]

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any], **kwds: Any) -> Self: ...
    def generate_raw_commands(self) -> Dict[str, Any]: ...
    @overload
    def register_command(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_command(
        self, __name: Optional[str] = ..., *, alias: Union[Iterable[str], str] = ..., **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_text(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_text(
        self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_number(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_number(
        self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    @overload
    def register_annotation(
        self, __func: Callable[..., Any], **kwds) -> Command: ...
    @overload
    def register_annotation(
        self, *, alias: Union[Iterable[str], str] = ..., **kwds: Any
    ) -> Callable[[Callable[..., Any]], Command]: ...
    

class CommandSet(metaclass=CommandSetMeta):
    raw_command_set: Dict[str, Callable]
    _bound_command_set: Dict[str, Callable]

    def __init__(self) -> None: ...
    def get(self, __key: str, default: Optional[Callable] = ...) -> Optional[Callable]: ...
    def __kola_caller__(self, command: Command, args: tuple, kwargs: Dict[str, Any], **kwds) -> Any: ...
    def __getitem__(self, __key: str) -> Callable: ...

