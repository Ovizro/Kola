from unittest import TestCase

from kola.lexer import StringLexer
from kola.parser import Parser
from kola.klvm import CommandSet, Environment, KoiLang, kola_command, kola_annotation, kola_env_enter, kola_env_exit, kola_text
from kola.klvm.decorator import kola_environment


class CommandSetTest(CommandSet):
    @kola_command
    def cmd1(self) -> int:
        return 1

    @kola_command
    def cmd2(self, s: str) -> int:
        return int(s)


@CommandSetTest.register_command(alias="cmd4")
def cmd3(vmobj: CommandSet) -> int:
    return 3


class EnvTest(KoiLang):
    @kola_command
    def version(self, __ver: int) -> int:
        return __ver

    class NumberEnv(Environment):
        @kola_env_enter("@number")
        def number(self, id: int) -> int:
            return id
        
        @kola_text
        def text(self, text: str) -> str:
            return f"text: {text}"
        
        @kola_environment
        class SubEnv:
            @kola_env_enter
            def enter(self) -> int:
                return 5
            
            @kola_env_exit
            def exit(self) -> int:
                return 6


class KolaTest(KoiLang, command_threshold=2):
    @kola_command
    def version(self, __ver: int) -> int:
        return __ver

    @kola_text
    def text(self, string: str) -> str:
        return f"text: {string}"
    
    @kola_annotation
    def annotation(self, string: str) -> str:
        return f"annotation: {string}"
            

class TestKoiLang(TestCase):
    def test_init(self) -> None:
        self.assertEqual(len(KoiLang.__command_field__), 3)
        self.assertEqual(KoiLang.__command_threshold__, 1)
        self.assertEqual(KoiLang.__text_encoding__, "utf-8")
        self.assertEqual(KolaTest.__command_threshold__, 2)

    def test_commandset(self) -> None:
        string = """
        #cmd1
        #cmd2 "2"
        #cmd3
        #cmd4
        """
        r = list(Parser(StringLexer(string), CommandSetTest()))
        self.assertEqual(r, [1, 2, 3, 3])

    def test_env(self) -> None:
        string = """
        #version 100
        #1
            Hello world!
        #2
            ???

            #enter
        """
        vmobj = EnvTest()
        ret = list(vmobj.parse(string, with_ret=True))
        self.assertIsInstance(vmobj.top, EnvTest.NumberEnv.SubEnv)
        self.assertEqual(
            ret,
            [100, 1, "text: Hello world!", 2, "text: ???", 5]
        )
        vmobj.parse("#exit")
        self.assertIs(vmobj.top, vmobj)
    
    def test_mainlang(self) -> None:
        string = """
        ##version 200

        # This is a text
        This is a text, too
        ### This is an annotation
        """
        vmobj = KolaTest()
        self.assertEqual(
            list(vmobj.parse(string, with_ret=True)),
            [200, "text: # This is a text", "text: This is a text, too", "annotation: ### This is an annotation"]
        )
