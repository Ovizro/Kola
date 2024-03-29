import os
from shutil import rmtree
from unittest import TestCase

from kola.klvm import KoiLang, kola_command
from kola.writer import WF_COMPLEX_ITEM, WI_NEWLINE, BaseWriter, ComplexArg, FileWriter, StringWriter, WF_ARG_ITEM


class TestWriter(TestCase):
    def setUp(self) -> None:
        os.makedirs("./test-tmp/", exist_ok=True)

    def tearDown(self) -> None:
        if os.path.isdir("test-tmp"):
            rmtree("test-tmp", ignore_errors=True)

    def test_init(self) -> None:
        with self.assertRaises(NotImplementedError):
            BaseWriter()
        with StringWriter() as w:
            self.assertFalse(w.closed)
            self.assertEqual(w.getvalue(), '')
        self.assertTrue(w.closed)
        with self.assertRaises(OSError):
            w.getvalue()
    
    def test_file(self) -> None:
        with FileWriter("test-tmp/01.kola") as w:
            self.assertFalse(w.closed)
            w.write_text("Hello world")
        self.assertTrue(w.closed)
        with self.assertRaises(OSError):
            w.write_text("Hello")
        with open("test-tmp/01.kola", encoding="utf-8") as fr:
            self.assertEqual(
                fr.read(),
                "Hello world\n"
            )
    
    def test_command(self) -> None:
        with StringWriter() as w:
            w.write_command(1)
            with self.assertRaises(ValueError):
                w.write_command(-10)
            with self.assertRaises(ValueError):
                w.write_command("10")
            w.write_command("echo", "Hello world", 114, 5.14, b"\"\\x20")
            w.write_command(
                "draw",
                "Line",
                WI_NEWLINE,
                ComplexArg("pos0", {'x': 0, 'y': 0}, split_line=True),
                pos1={'x': 16, 'y': 16},
                thickness=2,
                color=[255, 255, 255]
            )
            text = w.getvalue()
        self.assertEqual(
            text,
            "#1\n"
            "#echo \"Hello world\" 114 5.14 \"\\x20\n"
            "#draw Line \\\n    pos0(\\\n        x: 0, \\\n        y: 0\\\n    ) "
            "pos1(x: 16, y: 16) thickness(2) color(255, 255, 255)\n"
        )
    
    def test_item(self) -> None:
        class Item:
            def __kola_write__(self, writer: BaseWriter, level: int) -> None:
                writer.raw_write(str(level))
        
        with StringWriter() as w:
            i = Item()
            w.write_command("echo", i, complex=i)
            self.assertEqual(
                f"#echo {WF_ARG_ITEM} complex({WF_COMPLEX_ITEM})\n",
                w.getvalue()
            )
    
    def test_classwriter(self) -> None:
        class Vm(KoiLang):
            @kola_command
            def echo(self, text: str) -> None:
                print(text)
            
            @kola_command
            def help(self) -> None:  # type: ignore
                print("No, there is no help!")
            
            @help.set_data("writer_func")
            def help(writer: BaseWriter) -> None:  # type: ignore
                writer.write_command("help", "In fact, no help can be provided.")
            
            @kola_command
            def raw_write(self) -> None:
                ...
        
        with Vm.writer() as w:
            w.echo("Hello")
            with self.assertRaises(AttributeError):
                w.hello()
            w.help()
            self.assertEqual(
                w.getvalue(),
                "#echo Hello\n#help \"In fact, no help can be provided.\"\n"
            )
