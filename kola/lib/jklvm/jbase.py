import sys
from functools import wraps
from types import TracebackType
from typing import Any, Dict, Generator, NoReturn, Optional, Tuple, Type, Union

from kola.exception import KoiLangError
from kola.klvm import Command, CommandSet, kola_command, AbstractHandler
from kola.klvm.handler import ExceptionRecord
from kola.lib.recorder import Instruction

from .vm import JKoiLangVM, SectionInfo, VMState
from .exception import JKLvmException, JKLvmExit, JKLvmJump


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
    section: SectionInfo

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

    def goto(self, __addr_or_label: Union[int, str], *, absolute: bool = False) -> NoReturn:
        raise JKLvmJump(self.vm.eval_addr(__addr_or_label, absolute=absolute))
    
    def exit(self) -> NoReturn:
        raise JKLvmExit()
    
    add_label = _JKLvmMethod()
    get_label = _JKLvmMethod()
    has_label = _JKLvmMethod()
    
    @property
    def pc(self) -> int:
        pc = self.vm.pc
        assert pc - 1 in self.section
        return pc - self.section.start
    
    @kola_command("@command_exception", virtual=True)
    def on_command_exception(self, exc_type: Type[Exception], exc_ins: Optional[Exception], traceback: TracebackType) -> Any:
        if issubclass(exc_type, JKLvmExit):
            self.vm.exit()
            return True
        elif issubclass(exc_type, JKLvmJump):
            assert isinstance(exc_ins, JKLvmJump)
            vm = self.vm
            addr = exc_ins.addr
            if vm.running:
                vm.goto(addr)
            else:
                self.exec(addr)
            return True
        return False
    
    @kola_command("@exception", virtual=True, suppression=True)
    def on_exception(self, exc_type: Type[KoiLangError], exc_ins: Optional[KoiLangError], traceback: TracebackType) -> Any:
        pass


class JHandler(AbstractHandler):
    __slots__ = []

    priority = 20

    owner: JBase

    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], manual_call: bool = False, **kwds: Any) -> Any:
        vm = self.owner.vm
        if VMState.FROZEN | VMState.RUNNING not in vm.state and not command.virtual and not manual_call:
            vm.add_instruction(Instruction(command.__name__, args, kwargs))
        elif VMState.SKIPPING in vm.state:
            return vm.skip_once()
        super().__call__(command, args, kwargs, **kwds)
