from functools import partialmethod
from types import MethodType
from typing import Any, Callable, Dict, Generator, Iterable, Tuple, Union, overload
from typing_extensions import Self, Protocol, runtime_checkable


class CommandCaller(Protocol):
    def __call__(self, __command: Any, __args: tuple, __kwargs: Dict[str, Any], **kwds: Any) -> Any: ...


@runtime_checkable
class CommandLike(Protocol):
    def __kola_command__(self) -> Generator[Tuple[str, Callable], None, None]: ...


class Command(object):
    __slots__ = ["__name__", "__func__", "suppression", "virtual", "alias", "extra_data"]

    def __init__(
        self,
        __name: str,
        func: Callable,
        *,
        alias: Union[Iterable[str], str] = (),
        suppression: bool = False,
        virtual: bool = False,
        **kwds: Any
    ) -> None:
        self.__name__ = __name
        self.__func__ = func
        self.alias = (alias,) if isinstance(alias, str) else tuple(alias)
        self.suppression = suppression
        self.virtual = virtual
        self.extra_data = kwds
    
    @overload
    def set_data(self, __name: str, value: Any) -> Self: ...
    @overload
    def set_data(self, __name: str) -> Callable[[Any], Self]: ...

    def set_data(self, __name: str, value: Any = None) -> Union[Self, Callable[[Any], Self]]:
        if value is not None:
            self.extra_data[__name] = value
            return self
        
        def wrapper(val: Any) -> Self:
            self.extra_data[__name] = val
            return self
        return wrapper

    writer = partialmethod(set_data, "writer_func")
    
    @classmethod
    def from_command(cls, command: "Command", **kwds: Any) -> Self:
        data = command.extra_data.copy()
        data.update(kwds)
        return cls(
            command.__name__,
            command.__func__,
            alias=command.alias,
            **data
        )
    
    @property
    def __wrapped__(self) -> Callable:  # pragma: no cover
        return self.__func__
    
    def __kola_command__(self, force: bool = False) -> Generator[Tuple[str, Self], None, None]:
        if not self.suppression or force:
            bound_func = self
            yield self.__name__, bound_func
            for i in self.alias:
                yield i, bound_func

    def __get__(self, ins: Any, owner: type) -> Any:
        if ins is None:
            return self
        elif self.virtual and (not hasattr(owner, "check_virtual") or ins.check_virtual(self)):
            return ins[self.__name__]
        return MethodType(self, ins)

    def __call__(self, vmobj: Any, *args: Any, **kwds: Any) -> Any:
        caller = getattr(vmobj, "__kola_caller__", None)
        if caller is None:  # pragma: no cover
            return self.__func__(vmobj, *args, **kwds)
        return caller(self, args, kwds, **self.extra_data)

    def __repr__(self) -> str:
        return f"<kola command {self.__name__} with {self.__func__}>"
