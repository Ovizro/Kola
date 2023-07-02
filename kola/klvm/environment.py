from functools import partial
from types import TracebackType
from typing import Any, Callable, Dict, Generator, Iterable, Optional, Set, Tuple, Type, TypeVar, Union, overload
from typing_extensions import Self

from ..exception import KoiLangError

from .command import Command
from .commandset import CommandSet, CommandSetMeta


T = TypeVar("T")


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
    def from_command(cls, command: "Command", **kwds: Any) -> Self:
        if isinstance(command, EnvironmentCommand):
            kwds["env_class"] = command.env_class
        return super().from_command(command, **kwds)


class EnvironmentEntry(EnvironmentCommand):
    __slots__ = []
    
    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, suppression=True, **kwds)
    
    def __get__(self, ins: Any, owner: type) -> Any:
        assert self.env_class
        if isinstance(ins, self.env_class) and self.env_class.__env_autopop__:
            return EnvironmentAutopop.from_command(self).__get__(ins, owner)
        return super().__get__(ins, owner)

    def __call__(self, vmobj: Union["Environment", "KoiLang"], *args: Any, **kwds: Any) -> Any:
        assert self.env_class
        home = vmobj.home
        env = home.push_prepare(self.env_class)
        ret = super().__call__(env, *args, **kwds)
        home.push_apply(env)
        return ret


class EnvironmentExit(EnvironmentCommand):
    __slots__ = []

    def __call__(self, vmobj: "Environment", *args: Any, **kwds: Any) -> Any:
        home = vmobj.home
        pop_env = home.pop_prepare(self.env_class)
        ret = super().__call__(vmobj, *args, **kwds)
        home.pop_apply(pop_env)
        return ret


class EnvironmentAutopop(EnvironmentCommand):
    __slots__ = []

    def __call__(self, vmobj: "Environment", *args: Any, **kwds: Any) -> Any:
        assert self.env_class
        home = vmobj.home

        cache = home.pop_prepare(self.env_class)
        home.pop_apply(cache)
        cache = home.push_prepare(self.env_class)
        ret = super().__call__(cache, *args, **kwds)
        home.push_apply(cache)
        return ret


class EnvironmentMeta(CommandSetMeta):
    __env_entry__: Set[EnvironmentCommand]
    __env_exit__: Set[EnvironmentCommand]

    def __new__(cls, name: str, bases: Tuple[type, ...], attr: Dict[str, Any], **kwds: Any) -> Self:
        entry = set()
        exit = set()
        
        # Usually, there are not many entry points and exit points.
        # Therefore, unlike the attribute `__command_fields__`, they are computed here
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
    def __get__(self, ins: Any, owner: type) -> Self: ...
    @overload  # noqa: E301
    def __get__(
        self: Type[T],
        ins: Union["KoiLang", "Environment"],
        owner: Union[Type["KoiLang"], Type["Environment"]]
    ) -> T: ...
    def __get__(self, ins: Any, owner: type) -> Any:  # noqa: E301
        if ins is not None and issubclass(owner, CommandSet):
            home: KoiLang = ins.home
            cur = home.top
            while isinstance(cur, Environment):
                if cur.back is ins and isinstance(cur, self):
                    return cur
                cur = cur.back
            else:
                if ins is home.top:
                    return self.EntryPointInterface(self, ins)
                raise ValueError(f"cannot find env '{self.__name__}' in the {home}")
        return self
    
    class EntryPointInterface:
        """
        interface for entry points in Python level
        """
        __slots__ = ["__env_class", "__bound_ins"]

        def __init__(self, env_class: "EnvironmentMeta", bound_ins: CommandSet) -> None:
            self.__env_class = env_class
            self.__bound_ins = bound_ins
        
        def __getattr__(self, __name: str) -> Any:
            attr = getattr(self.__env_class, __name)
            if isinstance(attr, EnvironmentEntry):
                return attr.__get__(self.__bound_ins, self.__bound_ins.__class__)
            elif isinstance(attr, Command):
                raise AttributeError(f"cannot fetch command '{__name}' before the environment initialization")
            raise AttributeError("only entry commands can be accessed through the interface")
        
        def __repr__(self) -> str:  # pragma: no cover
            return f"<kola environment '{self.__env_class.__name__}' entry point command interface>"


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
                self.raw_command_set.update(
                    EnvironmentAutopop.from_command(c).__kola_command__()
                )

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
    
    def set_up(self, top: CommandSet) -> None:
        """called before the environment added to the env stack top"""

    def tear_down(self, top: CommandSet) -> None:
        """called after the environment removed from the env stack top"""

    @partial(Command, "@end")
    def at_end(self) -> None:
        """
        ensure autopop environments properly popped at the end of parsing
        """
        if not self.__class__.__env_autopop__:
            return
        home = self.home
        home.pop_apply(home.pop_prepare(self.__class__))
        home.at_end()
    
    @partial(Command, "@exception", virtual=True, suppression=True)
    def on_exception(self, exc_type: Type[KoiLangError], exc_ins: Optional[KoiLangError], traceback: TracebackType) -> Any:
        return self.back["@exception"]


from .koilang import KoiLang
