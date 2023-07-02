import sys
from types import TracebackType
from typing import Optional, Type
from traceback import print_exception

from kola import __version__
from kola.klvm import KoiLang, kola_command


class BaseDebugger(KoiLang):
    """
    provide unified version checking and error suppression functions
    """
    __slots__ = []

    @kola_command
    def version(self, __chk_ver: Optional[int] = None) -> None:
        if __chk_ver is None:
            print(__version__)
        elif __chk_ver < 100 or __chk_ver > 120:
            print(f"version {__chk_ver} is not support by runner {__version__}")
            sys.exit(2)

    def on_exception(self, exc_type: Type[BaseException], exc_ins: BaseException, traceback: TracebackType) -> bool:
        super().on_exception(exc_type, exc_ins, traceback)
        print_exception(exc_type, exc_ins, traceback)
        return True
