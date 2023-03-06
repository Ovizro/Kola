from unittest import TestCase

from kola.lexer import StringLexer
from kola.new_klvm.decorator import kola_env_exit
from kola.parser import Parser
from kola.new_klvm import CommandSet, Environment, KoiLang, kola_command, kola_env_enter, kola_text


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


class EnvTest0(KoiLang):
    @kola_command
    def version(self, __ver: int) -> int:
        assert __ver >= 100
        return __ver

    class NumberEnv(Environment):
        @kola_env_enter("@number")
        def number(self, id: int) -> int:
            return id
        
        @kola_text
        def text(self, text: str) -> str:
            return f"text: {text}"
        
        class SubEnv(Environment):
            @kola_env_enter
            def enter(self) -> int:
                return 5
            
            @kola_env_exit
            def exit(self) -> int:
                return 6
            

class TestKoiLang(TestCase):
    def test_commandset(self) -> None:
        string = """
        #cmd1
        #cmd2 "2"
        #cmd3
        #cmd4
        """
        r = list(Parser(StringLexer(string), CommandSetTest()))
        self.assertEqual(r, [1, 2, 3, 3])

    def test_env0(self) -> None:
        string = """
        #version 100
        #1
            Hello world!
        #2
            ???

            #enter
            #exit
        """
        vmobj = EnvTest0()
        ret = list(vmobj.parse(string, with_ret=True))
        self.assertIs(vmobj.top, vmobj)
        self.assertEqual(
            ret,
            [100, 1, "text: Hello world!", 2, "text: ???", 5, 6]
        )
