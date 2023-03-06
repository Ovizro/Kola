from typing import Any, Callable, Optional, Type, Union

from .commandset import Command
from .environment import EnvironmentCommand, EnvironmentEntry, EnvironmentExit


def _kola_decorator_factory(cmd_name: Optional[str] = None, cmd_type: Type[Command] = Command):
    def kola_env_enter(
        func: Union[Callable[..., Any], str, None] = None,
        **kwds
    ) -> Union[Command, Callable[[Callable], Command]]:
        def wrapper(wrapped_func: Callable[..., Any]) -> Command:
            nonlocal cmd_type
            if cmd_name is not None:
                assert not isinstance(func, str)
                name = cmd_name
            elif isinstance(func, str):
                name = func
            else:
                name = wrapped_func.__name__
            if "envs" in kwds and cmd_type is Command:
                cmd_type = EnvironmentCommand
            return cmd_type(name, wrapped_func, **kwds)
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    return kola_env_enter


kola_command = _kola_decorator_factory()
kola_text = _kola_decorator_factory("@text")
kola_number = _kola_decorator_factory("@number")
kola_annotation = _kola_decorator_factory("@annotation")
kola_env_enter = _kola_decorator_factory(cmd_type=EnvironmentEntry)
kola_env_exit = _kola_decorator_factory(cmd_type=EnvironmentExit)
