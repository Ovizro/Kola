from typing import Any, Callable, Iterable, Optional, overload, Union
from typing_extensions import Literal

from .commandset import Command
from .environment import EnvironmentEntry, EnvironmentExit


@overload
def kola_command(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_command(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_text(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_text(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_number(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_number(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_annotation(func: Callable[..., Any], **kwds) -> Command: ...
@overload
def kola_annotation(
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], Command]: ...
@overload
def kola_env_enter(func: Callable[..., Any], **kwds) -> EnvironmentEntry: ...
@overload
def kola_env_enter(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], EnvironmentEntry]: ...
@overload
def kola_env_exit(func: Callable[..., Any], **kwds) -> EnvironmentExit: ...
@overload
def kola_env_exit(
    func: Optional[str] = None,
    *,
    method: Literal["static", "class", "default"] = ...,
    envs: Union[Iterable[str], str] = ...,
    alias: Union[Iterable[str], str] = ...
) -> Callable[[Callable[..., Any]], EnvironmentExit]: ...
