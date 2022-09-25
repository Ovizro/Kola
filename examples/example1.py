import os
from typing import Union
from kola import KoiLang, BaseLexer, kola_command, kola_text, kola_env


class MultiFileManager(KoiLang):
    def __init__(self) -> None:
        super().__init__()
        self._file = None
    
    @kola_env
    def space(self, name: str) -> None:
        path = name.replace('.', '/')
        if not os.path.isdir(path):
            os.makedirs(path)
        os.chdir(path)
    
    @space.exit_command
    def endspace(self) -> None:
        os.chdir("..")
        self.end()
    
    @kola_command
    def file(self, path: str, encoding: str = "utf-8") -> None:
        if self._file:
            self._file.close()
        path_dir = os.path.dirname(path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        self._file = open(path, "w", encoding=encoding)
    
    @kola_command
    def end(self) -> None:
        if self._file:
            self._file.close()
            self._file = None
    
    @kola_text
    def text(self, text: str) -> None:
        if not self._file:
            raise OSError("write texts before the file open")
        self._file.write(text)
    
    def parse(self, lexer: Union[BaseLexer, str]) -> None:
        super().parse(lexer)
        self.end()


if __name__ == "__main__":
    MultiFileManager().parse_file("examples/example1.kola")