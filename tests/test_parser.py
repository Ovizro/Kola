from unittest import TestCase
from kola.exception import KoiLangSyntaxError
from kola.lexer import StringLexer
from kola.parser import Parser

from kola.lib.recorder import parse, parse_file, recorder


class TestParser(TestCase):
    def test_parser(self) -> None:
        parse_file("examples/example0.kola")

    def test_command(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang
            I am glad to meet you.
            ## And an annotation
            """
        )
        self.assertEqual(
            [i[0] for i in Parser(lexer, recorder)],
            ["hello", "@text", "@annotation"]
        )
        
    def test_number(self) -> None:
        parse(
            """
            #test t(0)
            #test t(0x0)
            #test t(0x0A)
            #test t(0b010)
            #test t(.0)
            #test t(1.)
            #test t(1.0e10)
            #test t(0e1)
            #test t(.0e-2)
            """
        )
    
    def test_recovery(self) -> None:
        lexer = StringLexer(
            """
            #err 0x01(x: 2)
            #hello "KoiLang\\u0020其他字段"
            I am glad to\\
 meet you.
            """
        )
        parser = Parser(lexer, recorder)
        with self.assertRaises(KoiLangSyntaxError):
            parser.exec()
        
        self.assertEqual(
            [i[1][0] for i in parser],
            ["KoiLang 其他字段", "I am glad to meet you."]
        )
    
    def test_recovery_syntax(self) -> None:
        lexer = StringLexer(
            """
            #err error.syntax
            #normal
            """
        )
        parser = Parser(lexer, recorder)
        with self.assertRaises(KoiLangSyntaxError):
            parser.exec()
        
        self.assertEqual(
            [i[0] for i in parser],
            ["normal"]
        )
        
    def test_recovery_syntax1(self) -> None:
        lexer = StringLexer(
            """
            #-err ## Content after that will be ignored
            #normal
            """
        )
        parser = Parser(lexer, recorder)
        with self.assertRaises(KoiLangSyntaxError):
            parser.exec()
        
        self.assertEqual(
            [i[0] for i in parser],
            ["normal"]
        )
    
    def test_err(self) -> None:
        lexer = StringLexer(
            """
            #err 0x01(x: 2)
            """
        )
        with self.assertRaises(KoiLangSyntaxError):
            Parser(lexer, recorder).exec()
