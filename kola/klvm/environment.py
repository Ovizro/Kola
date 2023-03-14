from typing import Any, Callable, Dict, Generator, Iterable, Optional, Set, Tuple, Type, Union, overload
from typing_extensions import Self

from .command import Command
from .commandset import CommandSet, CommandSetMeta


class EnvironmentCommand(Command):
    __slots__ = ["env_class"]

    def __init__(
        self,
        __name: str,
        func: Callable,
        env_class: Optional[Type["Environment"]] = None,
        envs: Union[Iterable[str], str, None] = None,
        **kwds
    ) -> None:
        super().__init__(__name, func, **kwds)
        if envs:
            self.extra_data["envs"] = (envs,) if isinstance(envs, str) else tuple(envs)
        self.env_class = env_class
    
    @classmethod
    def wrap_command(cls, command: "Command", **kwds) -> Self:
        data = command.extra_data.copy()
        data.update(kwds)
        return cls(
            command.__name__,
            command,
            alias=command.alias,
            **data
        )


class EnvironmentEntry(EnvironmentCommand):
    __slots__ = []
    
    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, suppression=True, **kwds)

    def __call__(self, vmobj: Union["Environment", "KoiLang"], *args: Any, **kwds: Any) -> Any:
        assert self.env_class
        vmobj.home.push(self.env_class)
        return super().__call__(vmobj, *args, **kwds)


class EnvironmentExit(EnvironmentCommand):
    __slots__ = []

    def __call__(self, vmobj: Union["Environment", "KoiLang"], *args: Any, **kwds: Any) -> Any:
        home = vmobj.home
        ret = super().__call__(vmobj, *args, **kwds)
        home.pop(self.env_class)
        return ret


class EnvironmentMeta(CommandSetMeta):
    __env_entry__: Set[EnvironmentCommand]
    __env_exit__: Set[EnvironmentCommand]

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any], **kwds: Any) -> Self:
        entry = set()
        exit = set()
        
        # usually, there are not many entry points and exit points.
        # so, no like attr `__command_field__`, I calculate these here.
        for i in bases:
            if not isinstance(i, EnvironmentMeta):
                continue
            entry.update(i.__env_entry__)
            exit.update(i.__env_exit__)

        attr["__env_entry__"] = entry
        attr["__env_exit__"] = exit
        new_cls = super().__new__(cls, name, bases, attr, **kwds)
        
        for v in attr.values():
            if not isinstance(v, EnvironmentCommand):
                continue
            v.env_class = new_cls  # type: ignore
            if isinstance(v, EnvironmentEntry):
                entry.add(v)
            elif isinstance(v, EnvironmentExit):
                exit.add(v)
        return new_cls
    
    @property
    def __env_autopop__(self) -> bool:
        return not self.__env_exit__
    
    def __kola_command__(self) -> Generator[Tuple[str, EnvironmentCommand], None, None]:
        for i in self.__env_entry__:
            yield from i.__kola_command__(force=True)

    @overload
    def __get__(self, ins: "KoiLang", owner: Type['KoiLang']) -> CommandSet: ...
    @overload
    def __get__(self, ins: Any, owner: type) -> Self: ...
    
    def __get__(self, ins: Any, owner: type) -> Any:
        if ins is not None and issubclass(owner, CommandSet):
            home: KoiLang = ins.home
            cur = home.top
            while isinstance(cur, Environment):
                if isinstance(cur, self) and isinstance(cur.back, owner):
                    return cur
                cur = cur.back
            else:
                raise ValueError(f"cannot find env '{self.__name__}' in the {home}")
        return self


class Environment(CommandSet, metaclass=EnvironmentMeta):
    __slots__ = ["back"]

    def __init__(self, back: CommandSet) -> None:
        if not self.__class__.__env_entry__:
            raise TypeError(
                "cannot instantiate an environment that has no entry points"
            )
        super().__init__()
        self.back = back

        if self.__class__.__env_autopop__:
            # for these have no exit point, use the same name as entry points
            for c in self.__class__.__env_entry__:
                self.raw_command_set.update(c.__kola_command__())

    def __getitem__(self, __key: str) -> Callable:
        cmd_set = self
        cmd = cmd_set.get(__key)
        while cmd is None:
            if not isinstance(cmd_set, Environment):
                raise KeyError(f"unknown command '{__key}'")
            cmd_set = cmd_set.back
            cmd = cmd_set.get(__key)
        return cmd
    
    def __kola_caller__(self, command: Command, args: tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        return self.home.__kola_caller__(command, args, kwargs, bound_instance=self, **kwds)

    @property
    def home(self) -> "KoiLang":
        cmd_set = self
        while isinstance(cmd_set, Environment):
            cmd_set = cmd_set.back
        assert isinstance(cmd_set, KoiLang)
        return cmd_set
    

from .koilang import KoiLang
