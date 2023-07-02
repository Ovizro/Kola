import os
from pathlib import Path
from shutil import rmtree
from typing import cast
from unittest import TestCase
from kola.lib.fastfiles import FastFiles


class TestFastFiles(TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.makedirs("./Temp", exist_ok=True)
    
    def tearDown(self) -> None:
        super().tearDown()
        rmtree("./Temp", ignore_errors=True)

    def test_init(self) -> None:
        ffs = FastFiles("./Temp")
        with ffs.exec_block():
            ffs.FileContains.open("file1.txt")
            ffs.FileContains.text("text in file1")
            ffs.FileContains.Space.enter("space2")

            self.assertIsInstance(ffs.top, FastFiles.Space)
            self.assertIsInstance(cast(ffs.Space, ffs.top).back, FastFiles)
            with self.assertRaises(ValueError):
                ffs.FileContains.open(Path("file2.txt"))
            ffs.Space.FileContains.open(Path("file2.txt"))
            ffs.Space.FileContains.text("text in file2")
        
        with open("./Temp/file1.txt") as f:
            self.assertEqual(f.read(), "text in file1")
        with open("./Temp/space2/file2.txt") as f:
            self.assertEqual(f.read(), "text in file2")
            

if __name__ == "__main__":
    TestFastFiles("test_init").run()
