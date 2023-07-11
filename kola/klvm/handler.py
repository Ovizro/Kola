from abc import ABC, abstractmethod
from operator import index as op_index
from threading import Lock
from typing import Any, ClassVar, Dict, Generator, Iterable, List, NamedTuple, Optional, SupportsIndex, Tuple, Type, TypeVar, Union
from typing_extensions import Self

from .mask import ClassNameMask, Mask
from .command import Command
from .commandset import CommandSet


_T_Handler = TypeVar("_T_Handler", bound="AbstractHandler")


class AbstractHandler(ABC):
    __slots__ = ["next", "owner"]

    priority: ClassVar[int] = 0

    def __init__(self, owner: "KoiLang", next: Optional["AbstractHandler"] = None) -> None:
        super().__init__()
        self.owner = owner
        self.next = next
    
    def insert(self, handler: _T_Handler) -> Union[Self, _T_Handler]:
        assert handler.next is None
        if self.priority <= handler.priority:
            handler.next = self
            return handler
        elif self.next is None:
            self.next = handler
        else:
            self.next = self.next.insert(handler)
        return self
    
    def remove(self, handler: _T_Handler) -> Union[Self, _T_Handler, None]:
        if self is handler:
            return self.next
        elif self.next:
            self.next = self.next.remove(handler)
            return self
        raise ValueError(f"{handler} is not in the handler chain")

    @abstractmethod
    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        if self.next is None:
            return
        return self.next(command, args, kwargs, **kwds)


class HandlerSequence:
    __slots__ = ["head"]

    def __init__(self, head: AbstractHandler) -> None:
        self.head = head
    
    def __getitem__(self, __index: SupportsIndex) -> AbstractHandler:
        hdl = self.__get(__index)
        if hdl is None:
            raise KeyError(__index)
        return hdl
    
    def __iter__(self) -> Generator[AbstractHandler, None, None]:
        head = self.head
        while head is not None:
            yield head
            head = head.next
    
    def __contains__(self, hdl: AbstractHandler) -> bool:
        if not isinstance(hdl, AbstractHandler):
            return NotImplemented
        return any(hdl is i for i in self)
    
    def __get(self, __index: SupportsIndex, default: Optional[AbstractHandler] = None) -> Optional[AbstractHandler]:
        i = op_index(__index)
        if i < 0:
            return list(self)[i]
        for hdl in self:
            if i == 0:
                return hdl
            i -= 1
        return default
    
    get = __get


def build_handlers(handlers: List[Type[AbstractHandler]], ins: Any) -> AbstractHandler:
    assert handlers
    base = handlers[0](ins)
    for i in handlers[1:]:
        hdl = i(ins)
        base = base.insert(hdl)
    return base


from .koilang import KoiLang


default_handler = KoiLang.register_handler


@default_handler
class CallerHandler(AbstractHandler):
    __slots__ = []

    def __call__(
        self,
        command: Command,
        args: Tuple,
        kwargs: Dict[str, Any],
        *,
        bound_instance: Optional[CommandSet] = None,
        **kwds: Any
    ) -> Any:
        ret = command.__func__(bound_instance or self.owner, *args, **kwargs)
        super().__call__(command, args, kwargs, bound_instance=bound_instance, ret_value=ret, **kwds)
        return ret


@default_handler
class SkipHandler(AbstractHandler):
    __slots__ = []

    priority = 10

    def __call__(
        self,
        command: Command,
        args: Tuple,
        kwargs: Dict[str, Any],
        *,
        skip: bool = False,
        **kwds: Any
    ) -> Any:
        if not skip:
            return super().__call__(command, args, kwargs, **kwds)


class _EnvChecker(NamedTuple):
    reachable: List[CommandSet]
    contains: List[CommandSet]

    def eval_masks(self, checker: CommandSet, names: Iterable[Union[str, Mask]]) -> List[Mask]:
        if isinstance(names, (str, Mask)):
            names = (names,)
        var_dict = {str(i): self.contains[i] for i in range(len(self.contains) - 1, -1, -1)}
        var_dict["top"] = self.contains[0]
        var_dict.update({'?': checker, "cur": checker, "current": checker})
        var_dict.update(base=self.contains[-1], __init__=self.contains[-1])
        return [i if isinstance(i, Mask) else ClassNameMask(i, **var_dict) for i in names]
    
    def ensure_envs(self, masks: List[Mask]) -> None:
        ng, pt = [], []
        for i in masks:
            if i.not_:
                ng.append(i)
            else:
                pt.append(i)

        if ((not ng or all(not self.check_mask(i) for i in ng)) and
                (not pt or any(self.check_mask(i) for i in pt))):
            return
        raise ValueError(f"unmatched environment name {self.reachable[0]}")  # pragma: no cover
    
    def check_mask(self, mask: Mask) -> bool:
        if mask.type == Mask.MType.default:
            env_set = self.reachable
        elif mask.type == Mask.MType.all:
            env_set = self.contains
        else:
            return self.reachable[0] in mask
        return any(i in mask for i in env_set)


@default_handler
class EnsureEnvHandler(AbstractHandler):
    __slots__ = []

    priority = 5

    def _eval_checker(self) -> _EnvChecker:
        reachable: List[CommandSet] = []
        top = self.owner.top
        while isinstance(top, Environment):
            reachable.append(top)
            if not top.__class__.__env_autopop__:
                contains = reachable.copy()
                while isinstance(top, Environment):
                    contains.append(top)
                    top = top.back
                contains.append(self.owner)
                break
            top = top.back
        else:
            # the base KoiLang object name is '__init__'
            reachable.append(self.owner)
            contains = reachable
        return _EnvChecker(reachable, contains)
    
    def __call__(
        self,
        command: Command,
        args: Tuple,
        kwargs: Dict[str, Any],
        *,
        bound_instance: Optional[CommandSet] = None,
        envs: Tuple[str, ...] = (),
        **kwds: Any
    ) -> Any:
        if envs:
            checker = self._eval_checker()
            masks = checker.eval_masks(bound_instance or self.owner, envs)
            checker.ensure_envs(masks)
        return super().__call__(command, args, kwargs, bound_instance=bound_instance, **kwds)


from .environment import Environment
