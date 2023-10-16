import sys
from typing import Any, Generator, Union, overload
from typing_extensions import Literal

from kola.exception import KoiLangError
from kola.lexer import BaseLexer, StringLexer
from kola.parser import Parser
from kola.klvm import KoiLang
from kola.lib.recorder import recorder

from .vm import JKoiLangVM, _loop
from .jbase import JBase


class JKoiLang(JBase, KoiLang):
    """
    a KoiLang implementation that can use global jump instructions
    """
    __slots__ = ["vm", "section"]

    @overload
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: Literal[False] = False, close_lexer: bool = True) -> None: ...
    @overload  # noqa: E301
    def parse(
        self,
        lexer: Union[BaseLexer, str],
        *,
        with_ret: Literal[True],
        close_lexer: bool = True
    ) -> Generator[Any, None, None]: ...
    def parse(self, lexer: Union[BaseLexer, str], *, with_ret: bool = False, close_lexer: bool = True) -> Any:  # noqa: E301
        if isinstance(lexer, str):
            if not close_lexer:
                raise ValueError("inner string lexer must be closed at the end of parsing")
            lexer = StringLexer(
                lexer,
                encoding=self.__class__.__text_encoding__,
                command_threshold=self.__class__.__command_threshold__,
                no_lstrip=not self.__class__.__text_lstrip__
            )
        
        # read all command info
        with self.exec_block():
            vm = self.vm
            parser = Parser(lexer, recorder)
            while True:
                try:
                    vm.codes.extend(parser)
                except KoiLangError:
                    if not self.on_exception(*sys.exc_info()):
                        if close_lexer:
                            lexer.close()
                        raise
                else:
                    break
            if close_lexer:
                lexer.close()
            
            # start execution
            vm.freeze()
            gen = self.exec()
            if with_ret:
                return gen
            _loop(gen)
    
    def at_start(self) -> None:
        super().at_start()
        self.vm = JKoiLangVM()
        self.section = self.vm.cur_section
