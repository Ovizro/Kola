from functools import wraps
import sys
from types import TracebackType
from typing import Any, Dict, Generator, NoReturn, Optional, Tuple, Type, Union

from kola.exception import KoiLangError
from kola.klvm import Command, CommandSet, kola_command, AbstractHandler
from kola.klvm.handler import ExceptionRecord
from kola.lib.recorder import Instruction

from .vm import JKoiLangVM, _loop, VMState
from .exception import JKLvmException, JKLvmAddressError, JKLvmAddressFault, JKLvmExit, JKLvmJump


class _JKLvmMethod:
    __slots__ = ["__name__"]

    def __init__(self, name: Optional[str] = None) -> None:
        if name is not None:
            self.__name__ = name

    def __set_name__(self, owner: Type["JBase"], name: str) -> None:
        if not hasattr(self, "__name__"):
            self.__name__ = name
    
    def __get__(self, ins: Optional["JBase"], owner: Type["JBase"]) -> Any:
        if ins is None:
            func = getattr(JKoiLangVM, self.__name__)
            @wraps(func)
            def wrapper(self: JBase, *args, **kwds) -> Any:
                return func(self.vm, *args, **kwds)
            return wrapper
        return getattr(ins.vm, self.__name__)


class JBase(CommandSet):
    """
    base class for JKLvm classes
    """
    __slots__ = []

    vm: JKoiLangVM

    def __init__(self) -> None:
        super().__init__()
        self.offset = 0
        self.length = 0
        
    def exec(self, pc: int = 0) -> Generator[Any, None, None]:
        for name, args, kwargs in self.vm.run(pc=pc):
            try:
                ret = self[name](*args, **kwargs)
                if isinstance(ret, ExceptionRecord) and isinstance(ret.exception, JKLvmException):
                    continue
                yield ret
            except KoiLangError:
                if not self.on_exception(*sys.exc_info()):
                    raise
    
    add_label = _JKLvmMethod()
    
    def goto(self, __addr_or_label: Union[int, str]) -> NoReturn:
        raise JKLvmJump(__addr_or_label)
    
    def exit(self) -> NoReturn:
        raise JKLvmExit(0, target=self)
    
    @property
    def pc(self) -> int:
        assert self.offset <= self.vm.pc < self.offset + self.length
        return self.vm.pc - self.offset
    
    @pc.setter
    def pc(self, val: int) -> None:
        assert val >= 0 and (not self.length or val < self.length), "the value of pc out of range"
        self.vm.goto(val + self.offset, absolute=True)
    
    @kola_command("@exception", virtual=True)
    def on_exception(self, exc_type: Type[KoiLangError], exc_ins: Optional[KoiLangError], traceback: TracebackType) -> Any:
        if issubclass(exc_type, JKLvmExit):
            # set the value of the ip register to the length of
            # the code cache to make JKlvm exit the loop.
            self.vm.skip_until(-1, )
            return True
        elif issubclass(exc_type, JKLvmJump):
            assert isinstance(exc_ins, JKLvmJump)
            addr = exc_ins.target
            if addr == len(self.vm.codes):  # pragma: no cover
                raise JKLvmAddressError("instruction access out of bounds")
            self.vm.goto(addr)
            return True
        elif issubclass(exc_type, JKLvmAddressFault):
            assert isinstance(exc_ins, JKLvmAddressFault)
            _loop(self.exec())
        return False


class JHandler(AbstractHandler):
    __slots__ = ["vm"]

    priority = 20

    def bound_vm(self, vm: JKoiLangVM) -> None:
        self.vm = vm

    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], manual_call: bool = False, **kwds: Any) -> Any:
        vm = self.vm
        if VMState.FROZEN | VMState.RUNNING not in vm.state and not command.virtual and not manual_call:
            vm.add_instruction(Instruction(command.__name__, args, kwargs))
        elif VMState.SKIPPING not in vm.state:
            return super().__call__(command, args, kwargs, **kwds)
