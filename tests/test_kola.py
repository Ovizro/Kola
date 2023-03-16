from unittest import TestCase, runner

from kola.lexer import StringLexer
from kola.parser import Parser
from kola.klvm import CommandSet, Environment, KoiLang, kola_command, kola_annotation, kola_env_enter, kola_env_exit, kola_text
from kola.klvm.decorator import kola_environment
from kola.klvm.writer import KoiLangWriter


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
    __slots__ = []

    @kola_command
    def version(self, __ver: int) -> int:
        return __ver

    class NumberEnv(Environment):
        id: int

        @kola_env_enter("@number")
        def number(self, id: int) -> int:
            assert not hasattr(self, "id")
            self.id = id
            return id
        
        @kola_text
        def text(self, text: str) -> str:
            return f"[{self.id}] text: {text}"
        
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
            [100, 1, "[1] text: Hello world!", 2, "[2] text: ???", 5]
        )
        with vmobj.exec_body():
            ret = vmobj.NumberEnv.SubEnv.exit()  # type: ignore
            self.assertEqual(ret, 6)
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
    
    def test_writer(self) -> None:
        writer = KolaTest.writer
        self.assertTrue(issubclass(writer, KoiLangWriter))
        self.assertTrue(issubclass(writer, KolaTest))
        with writer() as wr:
            with self.assertRaises(TypeError):
                wr.version()
            wr.version(120)
            wr.text("Hello")
            wr.annotation("?")
            text = wr.getvalue()
        self.assertEqual(text, "##version 120\nHello\n###?\n")

    def test_writer2(self) -> None:
        with EnvTest.writer() as wr:
            wr.version(10)
            with self.assertRaises(AttributeError):
                wr.NumberEnv.text("Hello")
            wr.NumberEnv.number(1)
            wr.NumberEnv.text("Hello world!")
            wr.NumberEnv.number(2)
            wr.NumberEnv.text("???")
            wr.newline()
            wr.NumberEnv.SubEnv.enter()
            text = wr.getvalue()
        
        string = (
            "#version 10\n"
            "#1\n"
            "    Hello world!\n"
            "#2\n"
            "    ???\n"
            "    \n"
            "    #enter\n"
        )
        self.assertEqual(text, string)


if __name__ == "__main__":
    for i in TestKoiLang.__dict__:
        if i.startswith("test_"):
            TestKoiLang(i).run()
