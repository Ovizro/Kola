from types import TracebackType
from typing import Any, Callable, Dict, NoReturn, Optional, Type

from kola.exception import KoiLangError
from kola.klvm import Command, CommandSet, Environment, KoiLang
from kola.lib.envutils import HandlerEnv

from .vm import JKoiLangVM, SectionInfo, VMState
from .jbase import JBase
from .exception import JKLvmExit, JKLvmAddressError


class JEnvironment(JBase, Environment):
    """
    an environemnt implementation that can use jump instructions in the environment
    """
    __slots__ = ["vm", "section", "_shutting_down"]

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
        self.vm = vm
        self.section = vm.fetch_section(vm.pc)
    
    def exit(self) -> NoReturn:
        self._shutting_down = True
        return super().exit()
    
    def tear_down(self, top: CommandSet) -> None:
        if VMState.SKIPPING in self.vm.state and self._shutting_down:
            self.vm.state &= ~VMState.SKIPPING
        super().tear_down(top)
        section = self.section
        if not section.length:
            section.length = self.pc
        self.vm.release_section(self.section)


from .jkoilang import JKoiLang
