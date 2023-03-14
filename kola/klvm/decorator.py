from types import new_class
from typing import Any, Callable, Optional, Type, Union

from .command import Command
from .commandset import CommandSet
from .environment import Environment, EnvironmentEntry, EnvironmentExit
from .koilang import KoiLang


def _kola_decorator_factory(cmd_name: Optional[str] = None, cmd_type: Type[Command] = Command):
    def kola_decorator(
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
            return cmd_type(name, wrapped_func, **kwds)
        if callable(func):
            return wrapper(func)
        else:
            return wrapper
    return kola_decorator


kola_command = _kola_decorator_factory()
kola_text = _kola_decorator_factory("@text")
kola_number = _kola_decorator_factory("@number")
kola_annotation = _kola_decorator_factory("@annotation")
kola_env_enter = _kola_decorator_factory(cmd_type=EnvironmentEntry)
kola_env_exit = _kola_decorator_factory(cmd_type=EnvironmentExit)


def _kola_class_decorator_factory(base: Type[CommandSet] = CommandSet):
    def kola_class_decoractor(kola_cls: Union[Type[KoiLang], str, None] = None, **kwds):
        def wrapper(wrapped_class: Type) -> Type[CommandSet]:
            if isinstance(kola_cls, str):
                env_name = kola_cls
            else:
                env_name = wrapped_class.__name__
            
            return new_class(
                env_name,
                (base,),
                kwds,
                lambda attrs: attrs.update(wrapped_class.__dict__)
            )
        if isinstance(kola_cls, type):
            return wrapper(kola_cls)
        else:
            return wrapper
    return kola_class_decoractor


kola_command_set = _kola_class_decorator_factory()
kola_environment = _kola_class_decorator_factory(Environment)
kola_main = _kola_class_decorator_factory(KoiLang)
