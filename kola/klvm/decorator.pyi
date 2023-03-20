from typing import Any, Callable, Iterable, Optional, Type, overload, Union
from typing_extensions import Literal

from .commandset import Command, CommandSet
from .environment import Environment, EnvironmentEntry, EnvironmentExit
from .koilang import KoiLang


@overload
def kola_command(func: Callable[..., Any], **kwds: Any) -> Command: ...
@overload
def kola_command(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_text(func: Callable[..., Any], **kwds: Any) -> Command: ...
@overload
def kola_text(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_number(func: Callable[..., Any], **kwds: Any) -> Command: ...
@overload
def kola_number(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_annotation(func: Callable[..., Any], **kwds: Any) -> Command: ...
@overload
def kola_annotation(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_env_enter(func: Callable[..., Any], **kwds: Any) -> EnvironmentEntry: ...
@overload
def kola_env_enter(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], EnvironmentEntry]: ...
@overload
def kola_env_exit(func: Callable[..., Any], **kwds: Any) -> EnvironmentExit: ...
@overload
def kola_env_exit(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...,
    **kwds: Any
) -> Callable[[Callable[..., Any]], EnvironmentExit]: ...
@overload
def kola_command_set(kola_cls: Type, **kwds: Any) -> Type[CommandSet]: ...
@overload
def kola_command_set(kola_cls: Optional[str] = None, **kwds: Any) -> Callable[[Type], Type[CommandSet]]: ...
@overload
def kola_environment(kola_cls: Type, **kwds: Any) -> Type[Environment]: ...
@overload
def kola_environment(kola_cls: Optional[str] = None, **kwds: Any) -> Callable[[Type], Type[Environment]]: ...
@overload
def kola_main(kola_cls: Type, **kwds: Any) -> Type[KoiLang]: ...
@overload
def kola_main(kola_cls: Optional[str] = None, **kwds: Any) -> Callable[[Type], Type[KoiLang]]: ...
