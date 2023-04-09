from unittest import TestCase
from kola.exception import KoiLangSyntaxError
from kola.lexer import StringLexer, FileLexer, Token, S_CMD, S_LITERAL, S_ANNOTATION, S_TEXT, F_DISABLED, F_LSTRIP_TEXT


class TestLexer(TestCase):
    def test_init(self) -> None:
        lexer = FileLexer("examples/example0.kola")
        self.assertFalse(lexer.closed)
        list(lexer)
        lexer.close()
        self.assertTrue(lexer.closed)

        with self.assertRaises(OSError):
            next(lexer)
        
        with self.assertRaises(TypeError):
            type("Temp", (Token,), {})

    def test_token(self) -> None:
        lexer = StringLexer(
            """
            #hello KoiLang
            I am glad to meet you.
            1
            ## And an annotation
            """
        )
        self.assertListEqual(
            list(lexer),
            [S_CMD, S_LITERAL, S_TEXT, S_TEXT, S_ANNOTATION]
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
    
    def test_command_threshold(self) -> None:
        lexer = StringLexer(
            "# #This is text\n"
            "##command\n"
            "### And an annotation\n",
            command_threshold=2
        )
        self.assertEqual(
            list(lexer),
            [S_TEXT, S_CMD, S_ANNOTATION]
        )
    
    def test_config(self) -> None:
        lexer = StringLexer(
            "#command\n"
            # switch to 'threshold=2'
            "   #text\n"
            # switch to 'no_lstrip=True'
            "   #text2\n"
            # switch to 'diabled=True'
            "EOF"
        )
        it = iter(lexer)
        self.assertEqual(next(it), S_CMD)
        lexer.config.command_threshold = 2
        self.assertEqual(next(it).val, "#text")
        lexer.config.no_lstrip = True
        self.assertEqual(next(it).val, "   #text2")
        lexer.config.disabled = True
        with self.assertRaises(OSError):
            next(it)
        self.assertTrue(lexer.closed)
        self.assertEqual(
            lexer.config.data_names,
            {'command_threshold', 'disabled', 'encoding', 'filename', 'flag', 'lexer', 'no_lstrip'}
        )
        self.assertIsInstance(lexer.config.data_names, frozenset)
        self.assertEqual(
            lexer.config.dict(),
            {
                "filename": "<string>",
                "encoding": "utf-8",
                "command_threshold": 2,
                "flag": F_DISABLED | F_LSTRIP_TEXT,
                "lexer": lexer,
                "disabled": True,
                "no_lstrip": True
            }
        )
