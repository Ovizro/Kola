from unittest import TestCase
from kola.exception import KoiLangSyntaxError
from kola.lexer import StringLexer, FileLexer, S_CMD, S_LITERAL, S_TEXT, Token


class TestLexer(TestCase):
    def test_init(self) -> None:
        lexer = FileLexer("examples/example0.kola")
        list(lexer)
        lexer.close()

        with self.assertRaises(OSError):
            next(lexer)
        
        with self.assertRaises(TypeError):
            type("Temp", (Token,), {})

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
    
    def test_encoding(self) -> None:
        text = "这是一段中文文本"
        btext = text.encode("gbk")
        with self.assertRaises(UnicodeError):
            token, = StringLexer(btext)
        with self.assertRaises(UnicodeError):
            token, = StringLexer(btext, encoding="utf-8")
        token, = StringLexer(btext, encoding="gbk")
        self.assertEqual(token.syn, S_TEXT)
        self.assertEqual(token.val, text)

        test_string = r"\u00a7a呃，\x20只熟悉这一个Unicode"
        self.assertEqual(test_string[0], '\\')
        _, t_str = StringLexer(f'#command "{test_string}"')
        self.assertNotEqual(t_str.val, test_string)
        self.assertEqual(t_str.val, eval(f"'{test_string}'"))
