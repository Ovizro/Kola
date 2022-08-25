from unittest import TestCase
from kola.exception import KoiLangSyntaxError
from kola.lexer import FileLexer, StringLexer
from kola.parser import Parser

from .util import CommandTest


class TestParser(TestCase):
    def test_parser(self) -> None:
        lexer = FileLexer("examples/example0.kola")
        Parser(lexer, CommandTest).exec_()

    def test_command(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang
            I am glad to meet you.
            """
        )
        self.assertEqual(
            [i[0] for i in Parser(lexer, CommandTest)], 
            ["hello", "@text"]
        )
    
    def test_recovery(self) -> None:
        lexer = StringLexer(
            """
            #err 0x01(x: 2)
            #hello KoiLang
            I am glad to meet you.
            """
        )
        parser = Parser(lexer, CommandTest)
        with self.assertRaises(KoiLangSyntaxError):
            parser.exec_()
        
        self.assertEqual(
            [i[0] for i in parser], 
            ["hello", "@text"]
        )
    
    def test_err(self) -> None:
        lexer = StringLexer(
            """
            #err 0x01(x: 2)
            """
        )
        with self.assertRaises(KoiLangSyntaxError):
            Parser(lexer, CommandTest).exec_()