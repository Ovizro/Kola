import os
from functools import partial
from types import TracebackType
from typing import Any, Dict, Tuple, Type
from unittest import TestCase

from kola.klvm import CommandSet, Environment, KoiLang
from kola.klvm.command import Command
from kola.klvm.decorator import kola_command, kola_environment, kola_annotation, kola_text, kola_env_enter, kola_env_exit
from kola.klvm.writer import KoiLangWriter
from kola.klvm.handler import AbstractHandler, SkipHandler
from kola.lexer import StringLexer
from kola.parser import Parser
from kola.writer import BaseWriter


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
        __slots__ = ["id"]

        @kola_env_enter("@number", envs=("__init__", "!+number"))
        def number(self, id: int) -> int:
            assert not hasattr(self, "id")
            self.id = id
            return id
        
        @kola_text
        def text(self, text: str) -> str:
            return f"[{self.id}] text: {text}"
        
        @kola_environment()
        class SubEnv:
            @kola_env_enter
            def enter(self) -> int:
                return 5
            
            @kola_env_exit
            def exit(self) -> int:
                return 6


class KolaTest(KoiLang, command_threshold=2, lstrip_text=False):
    @kola_command(envs="+$0")
    def version(self, __ver: int) -> int:  # type: ignore
        return __ver
    
    @version.writer
    def version(writer: BaseWriter, __ver: int) -> None:  # type: ignore
        writer.write_command("version", 120)

    @kola_text
    def text(self, string: str) -> str:
        return f"text: {string}"
    
    @kola_annotation
    def annotation(self, string: str) -> str:
        return f"annotation: {string}"
    
    def at_start(self) -> None:
        self.errors = []
        return super().at_start()

    def on_exception(self, exc_type: Type[BaseException], exc_ins: BaseException, traceback: TracebackType) -> bool:
        self.errors.append(exc_ins.__cause__)
        super().on_exception(exc_type, exc_ins, traceback)
        return True


class Handler1(AbstractHandler):
    priority = 1

    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        super().__call__(command, args, kwargs, **kwds)
        return 1


class Handler2(AbstractHandler):
    priority = 2

    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        super().__call__(command, args, kwargs, **kwds)
        return 2
            

class TestKoiLang(TestCase):
    def test_init(self) -> None:
        self.assertEqual(len(KoiLang.__command_field__), 3)
        self.assertEqual(KoiLang.__command_threshold__, 1)
        self.assertEqual(KoiLang.__text_encoding__, "utf-8")
        self.assertEqual(KolaTest.__command_threshold__, 2)
        with self.assertRaises(TypeError):
            Environment(CommandSet())
        KoiLang().parse("")

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
        with vmobj.exec_block():
            ret = vmobj.NumberEnv.SubEnv.exit()  # type: ignore
            self.assertEqual(ret, 6)
        self.assertIs(vmobj.top, vmobj)
    
    def test_mainlang(self) -> None:
        string = (
            "##version 200\n"
            "\n"
            "# This is a text\n"
            "   This is a text, too\n"
            "##error \"Raise an error\"\n"
            "### This is an annotation\n"
        )
        vmobj = KolaTest()
        self.assertEqual(
            list(vmobj.parse(string, with_ret=True)),
            [200, "text: # This is a text", "text:    This is a text, too", "annotation: ### This is an annotation"]
        )
        self.assertEqual(vmobj.errors, [None])
    
    def test_writer(self) -> None:
        writer = KolaTest.writer
        self.assertIs(writer, KolaTest.writer)
        self.assertTrue(issubclass(writer, KoiLangWriter))
        self.assertTrue(issubclass(writer, KolaTest))

        path = "tests/tmp.kola"
        with writer(path) as wr:
            self.addCleanup(partial(os.remove, path))
            with self.assertRaises(TypeError):
                wr.version()
            wr.version(10)
            wr.text("Hello")
            wr.annotation("?")
        ret = list(KolaTest().parse_file(path, with_ret=True))
        self.assertEqual(ret, [120, "text: Hello", "annotation: ###?"])

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
    
    def test_handler(self) -> None:
        vmobj = KolaTest()
        self.assertIsInstance(vmobj._handler.next, SkipHandler)
        self.assertEqual(vmobj.version(100), 100)
        hdl1 = vmobj.add_handler(Handler1)
        self.assertIs(vmobj.handlers[4], hdl1)
        self.assertIs(vmobj.handlers[-2], hdl1)
        self.assertEqual(vmobj.version(100), 1)
        hdl2 = vmobj.add_handler(Handler2)
        self.assertIs(vmobj.handlers[4], hdl2)
        self.assertEqual(vmobj.version(100), 2)
        vmobj.remove_handler(hdl1)
        self.assertNotIn(hdl1, vmobj.handlers)
        self.assertEqual(vmobj.version(100), 2)
        vmobj.remove_handler(hdl2)
        self.assertEqual(vmobj.version(100), 100)


if __name__ == "__main__":
    for i in TestKoiLang.__dict__:
        if i.startswith("test_"):
            TestKoiLang(i).run()
