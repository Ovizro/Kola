from unittest import TestCase
from kola.lexer import StringLexer
from kola.parser import Parser

from .util import CommandTest


class TestParser(TestCase):
    
    def test_parser(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang pos(1, 2)
            I am glad to meet you.
            """
        )
        for _ in Parser(lexer, CommandTest):
            pass