import os
from shutil import rmtree
from unittest import TestCase
from kola.writer import BaseWriter, FileWriter, StringWriter


class TestWriter(TestCase):
    def setUp(self) -> None:
        os.makedirs("./test-tmp/")

    def tearDown(self) -> None:
        if os.path.isdir("test-tmp"):
            rmtree("test-tmp", ignore_errors=True)

    def test_init(self) -> None:
        with self.assertRaises(NotImplementedError):
            BaseWriter()
    
    def test_file(self) -> None:
        with FileWriter("test-tmp/01.kola") as f:
            self.assertFalse(f.closed)
            f.write_text("Hello world")
        self.assertTrue(f.closed)
        with self.assertRaises(OSError):
            f.write_text("Hello")
        with open("test-tmp/02.kola", encoding="utf-8") as fr:
            self.assertEqual(
                fr.read(),
                "Hello world\n"
            )
