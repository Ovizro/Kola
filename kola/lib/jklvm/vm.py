from audioop import add
from collections import defaultdict
from contextlib import contextmanager
from enum import IntFlag, auto
from typing import Dict, Generator, Iterable, List, NamedTuple, Optional, Type, Union
from typing_extensions import Self

from kola.klvm import CommandSet, Environment
from kola.lib.recorder import Instruction


class VMState(IntFlag):
    INITIAL = 0
    RUNNING = auto()
    SKIPPING = auto()
    FROZEN = auto()


def _loop(__it: Iterable) -> None:
    """iterate an object until finish

    :param __it: object to iterate
    :type __it: Iterable
    """
    for _ in __it:
        ...


class SectionInfo(NamedTuple):
    start: int
    length: int = 0
    back: Optional["SectionInfo"] = None


class JKoiLangVM(object):
    __slots__ = ["state", "codes", "labels", "section_table", "cur_section", "_pc", "_skip_count"]

    codes: List[Instruction]
    labels: Dict[str, int]

    def __init__(self) -> None:
        self.state = VMState.INITIAL
        self._pc = 0
        self.codes = []
        self.labels = {}
        self.section_table = defaultdict(list)
        self.cur_section = SectionInfo(0)
        self.section_table[0].append(self.cur_section)
    
    def add_instruction(self, ins: Instruction) -> None:
        assert self.state == VMState.INITIAL, "cannot add new instructions when the vm is running"
        self.codes.append(ins)
    
    def add_label(self, name: str, offset: int = 0) -> None:
        if name in self.labels:
            raise ValueError("duplicate label")
        self.labels[name] = offset + self.pc
    
    def add_section(self, start: int, length: int = -1) -> None:
        section = SectionInfo(start, length, self.cur_section)
        self.cur_section = section
        self.section_table[section.start].append(section)
    
    def run(self, pc: int = 0) -> Generator[Instruction, None, None]:
        with self._run_block():
            self._pc = pc + len(self.codes) if pc < 0 else pc
            while self._pc != len(self.codes):
                pc = self._pc
                self._pc += 1
                yield self.codes[pc]
    
    def goto(self, offset: Union[int, str], *, absolute: bool = False) -> None:
        assert self.running, "cannot jump when the virtual machine is not running"
        if isinstance(offset, str):
            pc = self.labels[offset]
        else:
            pc = offset if absolute else offset + self.pc
        if pc < 0 or pc >= len(self.codes):
            raise ValueError(f"pc({pc}) out of range")
        self._pc = pc
    
    def skip_until(self, offset: int) -> None:
        if self.running:
            self.exit()
        self._skip_count = offset
    
    def exit(self) -> None:
        self._pc = len(self.codes)
    
    def freeze(self) -> None:
        self.state |= VMState.FROZEN
    
    @property
    def pc(self) -> int:
        return self._pc
    
    @property
    def running(self) -> bool:
        return VMState.RUNNING in self.state
    
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
