from types import TracebackType
from typing import Any, NoReturn, Optional, Type

from kola.klvm import CommandSet, Environment, kola_command
from kola.lib.envutils import HandlerEnv

from .vm import JKoiLangVM, VMState
from .jbase import JBase, JHandler
from .exception import JKLvmExit


class JEnvironment(JBase, HandlerEnv):
    """
    an environemnt implementation that can use jump instructions in the environment
    """
    __slots__ = ["vm", "section", "_shutting_down"]

    Handler = JHandler

    def exit(self) -> NoReturn:
        self._shutting_down = True
        super().exit()
    
    def set_up(self, top: CommandSet) -> None:
        super().set_up(top)
        while isinstance(top, Environment):
            if isinstance(top, JEnvironment):
                vm = top.vm
                break
            top = top.back
        else:
            if isinstance(top, JBase):
                vm = top.vm
            else:
                vm = JKoiLangVM()
                return
            
        if VMState.SKIPPING in vm.state:
            raise RuntimeError("cross-environment jumps are not possible")
        self.vm = vm
        self.section = vm.fetch_section()
    
    def tear_down(self, top: CommandSet) -> None:
        if VMState.SKIPPING in self.vm.state and self._shutting_down:
            self.vm.state &= ~VMState.SKIPPING
        super().tear_down(top)
        section = self.section
        if not section.length:
            section.length = self.pc
        self.vm.release_section(self.section)
    
    def _force_pop(self) -> None:
        home = self.home
        while home.top is not self:
            home.pop_apply(home.pop_prepare())
        home.pop_apply(home.pop_prepare())
    
    @kola_command("@command_exception", virtual=True)
    def on_command_exception(self, exc_type: Type[Exception], exc_ins: Optional[Exception], traceback: TracebackType) -> Any:
        if issubclass(exc_type, JKLvmExit):
            if self.section.length:
                start, length = self.section
                self.vm.goto(start + length)
                self._force_pop()
            else:
                self.vm.skip_until(-1)
            return True
        return super().on_command_exception(exc_type, exc_ins, traceback)
