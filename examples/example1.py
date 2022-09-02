import os
from typing import Optional, TextIO
from kola import KoiLang, kola_command, kola_text


class MultiFileManager(KoiLang):
    def __init__(self) -> None:
        super().__init__()
        self._file: Optional[TextIO] = None
    
    def __del__(self) -> None:
        if self._file:
            self._file.close()
    
    @kola_command
    def space(self, name: str) -> None:
        path = name.replace('.', '/')
        if not os.path.isdir(path):
            os.makedirs(path)
        os.chdir(path)
    
    @kola_command
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


if __name__ == "__main__":
    MultiFileManager().parse_file("examples/example1.kola")