from unittest import TestCase

from kola.exception import KoiLangCommandError
from kola.lexer import StringLexer
from kola.parser import Parser
from kola.old_klvm import KoiLang, kola_annotation, kola_command, kola_text, kola_env, kola_env_class


class KolaTest(KoiLang):
    @kola_command("step_1", method="static")
    def step1(num: float) -> bool:  # type: ignore
        return abs(num - 1.01) < 0.0001
    
    @kola_env(env_name="env1")
    def step_2(self, *, key1, key2) -> tuple:
        return key1, key2
    
    @step_2.env_command(method="class")
    def step_3(cls: type) -> type:  # type: ignore
        return cls

    @step_2.exit_command
    def step_4(self) -> str:
        return self.top[0]

    @kola_env_class("env2")
    class KolaTestEnv(KoiLang):
        @kola_text
        def enter(self, text: str) -> str:
            self.l_num = [text]
            return text
        
        @kola_command
        def step_6(self) -> int:
            return len(self.l_num)


class KolaTest1(KoiLang, command_threshold=2):
    @kola_text
    def text(self, text: str) -> str:
        return text

    @kola_command
    def echo(self, s: str) -> None:
        assert s == "This is a command."
    
    @kola_annotation
    def annotation(self, an: str) -> None:
        assert an == "### This is an annotation."


class TestKlvm(TestCase):
    def test_init(self) -> None:
        self.assertEqual(KoiLang.__command_field__, set())
        self.assertEqual(KoiLang.__command_threshold__, 1)
        self.assertEqual(KoiLang.encoding, "utf-8")
        self.assertEqual(KolaTest1.__command_threshold__, 2)

    def test_env(self) -> None:
        string = """
        #step_1 0.101E1
        #step_2 key1(hello, "world") key2(abc)
        #step_3
        #step_4
        #step_3
        
        Hello
        #step_6
        World
        #step_6
        """

        parser = Parser(StringLexer(string), KolaTest())
        self.assertTrue(parser.exec_once())  # step 1

        key1, key2 = parser.exec_once()  # step 2
        self.assertListEqual(key1, ["hello", "world"])
        self.assertEqual(key2, "abc")
        self.assertEqual(parser.exec_once(), KolaTest)  # step 3
        self.assertEqual(parser.exec_once(), "env1")  # step 4
        with self.assertRaises(KoiLangCommandError):
            parser.exec_once()  # step 3
        
        self.assertEqual(parser.exec_once(), "Hello")
        self.assertEqual(parser.exec_once(), 1)  # step 6
        self.assertEqual(len(parser.command_set), 2)
        self.assertEqual(parser.exec_once(), "World")
        self.assertEqual(parser.exec_once(), 1)  # step 6
    
    def test_threshold(self) -> None:
        string = """
        This is text.
        # #This is alse text.
        ### This is an annotation.
        ##echo "This is a command."
        """
        KolaTest1().parse(string)