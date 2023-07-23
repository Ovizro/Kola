from collections import defaultdict
from contextlib import contextmanager
from enum import IntFlag, auto
from typing import DefaultDict, Dict, Generator, Iterable, List, Optional,  Union
from typing_extensions import Self

from kola.klvm import CommandSet, Environment
from kola.lib.recorder import Instruction
from .exception import JKLvmAddressError


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


class SectionInfo:
    __slots__ = ["start", "length", "back"]

    def __init__(self, start: int, length: int = 0, back: Optional["SectionInfo"] = None) -> None:
        self.start = start
        self.length = length
        self.back = back
    
    def __iter__(self) -> Generator[int, None, None]:
        yield self.start
        yield self.length

    def __contains__(self, item: int) -> bool:
        if not isinstance(item, int):
            return NotImplemented
        start = self.start
        length = self.length
        return item >= start and (not length or item < length + start)
    
    def __repr__(self) -> str:
        start = self.start
        length = self.length
        if length:
            return f"<jklvm section from {start} to {start + length}>"
        else:
            return f"<jklvm section from {start}>"


class JKoiLangVM(object):
    __slots__ = ["state", "codes", "labels", "section_table", "cur_section", "_pc", "_skip_count"]

    codes: List[Instruction]
    labels: Dict[str, int]

    def __init__(self) -> None:
        self.state = VMState.INITIAL
        self._pc = 0
        self.codes = []
        self.labels = {}
        self.section_table: DefaultDict[int, List[SectionInfo]] = defaultdict(list)
        self.cur_section = SectionInfo(0)
        self.section_table[0].append(self.cur_section)
    
    def add_instruction(self, ins: Instruction) -> None:
        assert self.state == VMState.INITIAL, "cannot add new instructions when the vm is running"
        self.codes.append(ins)
    
    def add_label(self, name: str, offset: int = 0) -> None:
        if name in self.labels:
            raise ValueError("duplicate label")
        self.labels[name] = offset + self.pc
    
    def get_label(self, name: str) -> int:
        return self.labels[name]
    
    def have_label(self, name: str) -> bool:
        return name in self.labels
    
    def fetch_section(self, start: int, length: int = -1) -> SectionInfo:
        l_section = self.section_table[start]
        if start == self.cur_section.start and l_section[-1] is not self.cur_section:
            index = l_section.index(self.cur_section)
            return l_section[index + 1]
        section = SectionInfo(start, length, self.cur_section)
        self.cur_section = section
        l_section.append(section)
        return section

    def release_section(self, section: SectionInfo) -> None:
        cur = self.cur_section
        assert cur is section and cur.back
        if section.length == 0:
            raise ValueError("cannot release incomplete section")
        self.cur_section = cur.back
    
    def run(self, pc: int = 0) -> Generator[Instruction, None, None]:
        with self._run_block():
            self._pc = pc + len(self.codes) if pc < 0 else pc
            while self._pc != len(self.codes):
                pc = self._pc
                self._pc += 1
                yield self.codes[pc]
    
    def goto(self, pc: int) -> None:
        check_code = self._check_addr(pc)
        if check_code == 3:
            self.skip_until(pc)
        elif check_code:
            raise ValueError(f"pc({pc}) out of range")
        else:
            self._pc = pc
    
    def skip_until(self, offset: int) -> None:
        if self.running:
            self.exit()
        self.state |= VMState.SKIPPING
        self._skip_count = offset
    
    def exit(self) -> None:
        self._pc = len(self.codes)
    
    def freeze(self) -> None:
        self.state |= VMState.FROZEN
        self.section_table[0][0].length = len(self.codes)
    
    def _eval_addr(self, target: Union[int, str], *, absolute: bool = False) -> int:
        if isinstance(target, str):
            pc = self.labels[target]
        else:
            pc = target if absolute else target + self.pc
        return pc
    
    def _check_addr(self, addr: int) -> int:
        section = self.cur_section
        print(section)
        if addr not in section:
            return 1  # out of range
        elif any(
            any(addr in j for j in self.section_table[i] if j is not section)
            for i in self.section_table if i in section
        ):
            return 2  # target environment not initialized
        elif addr >= len(self.codes):
            return 3  # command not recorded
        return 0
    
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
