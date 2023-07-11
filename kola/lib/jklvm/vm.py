from contextlib import contextmanager
from enum import IntFlag, auto
from typing import Generator
from typing_extensions import Self

from kola.lib.recorder import Instruction


class VMState(IntFlag):
    INITIAL = 0
    RUNNING = auto()
    FROZEN = auto()


class JKoiLangVM(object):
    __slots__ = ["state", "codes", "_pc"]

    def __init__(self) -> None:
        self.state = VMState.INITIAL
        self._pc = 0
        self.codes = []
    
    def add_instruction(self, ins: Instruction) -> None:
        assert self.state == VMState.INITIAL, "cannot add new instructions when the vm is running"
        self.codes.append(ins)
    
    def run(self, pc: int = 0) -> Generator[Instruction, None, None]:
        with self._run_block():
            self._pc = pc + len(self.codes) if pc < 0 else pc
            while self._pc != len(self.codes):
                pc = self._pc
                self._pc += 1
                yield self.codes[pc]
    
    def goto(self, pc: int) -> None:
        assert self.running, "cannot jump when the virtual machine is not running"
        if pc < 0 or pc >= len(self.codes):
            raise ValueError(f"pc({pc}) out of range")
        self._pc = pc
    
    def exit(self) -> None:
        self._pc = len(self.codes)
    
    @property
    def pc(self) -> int:
        return self._pc
    
    @property
    def running(self) -> bool:
        return self.state in VMState.RUNNING
    
    @contextmanager
    def _run_block(self) -> Generator[Self, None, None]:
        if self.running:
            raise RuntimeError("JKLVM is already runing")
        self.state |= VMState.RUNNING
        try:
            yield self
        except:
            self.state &= ~VMState.RUNNING
            raise
