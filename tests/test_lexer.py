from unittest import TestCase
from kola.exception import KoiLangSyntaxError
from kola.lexer import StringLexer, FileLexer, S_CMD, S_LITERAL, S_TEXT


class TestLexer(TestCase):
    def test_init(self) -> None:
        lexer = FileLexer("examples/example0.kola")
        list(lexer)
        lexer.close()

        with self.assertRaises(OSError):
            next(lexer)

    def test_token(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang
            I am glad to meet you.
            """
        )
        self.assertListEqual(
            list(lexer),
            [S_CMD, S_LITERAL, S_TEXT]
        )
    
    def test_recovery(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang-
            I am glad to meet you.
            """
        )
        with self.assertRaises(KoiLangSyntaxError):
            list(lexer)
        
        self.assertEqual(next(lexer), S_TEXT)