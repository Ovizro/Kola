from typing import Any, Callable, Dict, Generator, Iterable, Optional, Set, Tuple, Type, Union, overload
from typing_extensions import Self

from ..exception import KoiLangCommandError
from .commandset import Command, CommandSet, CommandSetMeta


class EnvironmentCommand(Command):
    __slots__ = ["envs", "env_class"]

    def __init__(
        self,
        __name: str,
        func: Callable,
        env_class: Optional[Type["Environment"]] = None,
        envs: Union[Iterable[str], str] = tuple(),
        **kwds
    ) -> None:
        super().__init__(__name, func, **kwds)
        self.envs = (envs,) if isinstance(envs, str) else tuple(envs)
        self.env_class = env_class

    @classmethod
    def wrap_command(cls, command: "Command", **kwds) -> Self:
        return cls(
            command.__name__,
            command,
            alias=command.alias,
            method="default",
            env_class=command.env_class if isinstance(command, EnvironmentCommand) else None,
            **kwds
        )

    def __call__(self, vmobj: CommandSet, *args: Any, **kwds: Any) -> Any:
        if self.envs:
            if isinstance(vmobj, KoiLang):
                env_name = vmobj.top.__class__.__name__
            elif isinstance(vmobj, Environment):
                env_name = vmobj.__class__.__name__
            else:
                raise ValueError(
                    f"cannot check environments of '{vmobj.__class__.__qualname__}' object"
                )
            if env_name not in self.envs:
                raise KoiLangCommandError(f"unmatched environment {env_name}")
        return super().__call__(vmobj, *args, **kwds)


class EnvironmentEntry(EnvironmentCommand):
    __slots__ = []
    
    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, suppression=True, **kwds)

    def __call__(self, vmobj: Union["Environment", "KoiLang"], *args: Any, **kwds: Any) -> Any:
        assert self.env_class
        if isinstance(vmobj, Environment):
            back, home = vmobj, vmobj.home
        else:
            back, home = vmobj.top, vmobj
        new_env = self.env_class(back)
        home.push(new_env)
        return super().__call__(vmobj, *args, **kwds)


class EnvironmentExit(EnvironmentCommand):
    __slots__ = []

    def __call__(self, vmobj: Union["Environment", "KoiLang"], *args: Any, **kwds: Any) -> Any:
        if isinstance(vmobj, Environment):
            home = vmobj.home
        else:
            home = vmobj
        ret = super().__call__(vmobj, *args, **kwds)
        cur = home.pop()
        if self.env_class and not isinstance(cur, self.env_class):
            cur = home.top
            while isinstance(cur, Environment) and not cur.__class__.__env_entry__:
                if isinstance(cur, self.env_class):
                    break
                cur = home.pop()
            else:
                raise ValueError("unmatched environment")
        return ret


class EnvironmentMeta(CommandSetMeta):
    __env_entry__: Set[EnvironmentEntry]
    __env_exit__: Set[EnvironmentExit]

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
    
    def __kola_command__(self, cmd_set: CommandSet) -> Generator[Tuple[str, Callable], None, None]:
        for i in self.__env_entry__:
            yield from i.__kola_command__(cmd_set, force=True)

    @overload
    def __get__(self, ins: "KoiLang", owner: Type['KoiLang']) -> CommandSet: ...
    @overload
    def __get__(self, ins: Any, owner: type) -> Self: ...
    
    def __get__(self, ins: Any, owner: type) -> Any:
        if ins is not None:
            if isinstance(ins, KoiLang) and issubclass(owner, KoiLang):
                env_ins = ins.top
            elif isinstance(ins, Environment) and isinstance(owner, Environment):
                env_ins = ins.home.top
            else:
                return self
            assert isinstance(env_ins, self)
            return env_ins
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

        # for these have no exit point, use the same name as entry points
        if not self.__class__.__env_exit__:
            for entry in self.__class__.__env_entry__:
                for name, func in EnvironmentExit.wrap_command(entry).__kola_command__(self):
                    self.command_set[name] = func
            # wrap the `@end` command to ensure the environment being popped
            self.command_set["@end"] = EnvironmentExit(
                "@end", self["@end"], env_class=self.__class__, method="static"
            ).bind(self)

    def __getitem__(self, __key: str) -> Callable:
        cmd_set = self
        cmd = cmd_set.get(__key)
        while cmd is None:
            if not isinstance(cmd_set, Environment):
                raise KeyError(f"unknown command '{__key}'")
            cmd_set = cmd_set.back
            cmd = cmd_set.get(__key)
        return cmd

    @property
    def home(self) -> "KoiLang":
        cmd_set = self
        while isinstance(cmd_set, Environment):
            cmd_set = cmd_set.back
        assert isinstance(cmd_set, KoiLang)
        return cmd_set

    @property
    def next(self) -> "Environment":
        top = self.home.top
        while isinstance(top, Environment):
            if top.back is self:
                break
            top = top.back
        else:
            raise ValueError("next environment is not found")
        return top


from .koilang import KoiLang
