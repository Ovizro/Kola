import os
from kola import Environment, KoiLang, kola_command, kola_text, kola_env_enter, kola_env_exit


class FastFile(KoiLang):
    @kola_command
    def file(self, path: str, encoding: str = "utf-8") -> None:
        if self._file:
            self._file.close()
        path_dir = os.path.dirname(path)
        if path_dir:
            os.makedirs(path_dir, exist_ok=True)
        self._file = open(path, "w", encoding=encoding)
    
    class space(Environment):
        @kola_env_enter("space")
        def enter(self, name: str) -> None:
            self.pwd = os.getcwd()
            path = name.replace('.', '/')
            if not os.path.isdir(path):
                os.makedirs(path)
            os.chdir(path)
        
        @kola_env_exit("endspace")
        def exit(self) -> None:
            os.chdir(self.pwd)

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
    
    def at_start(self) -> None:
        super().at_start()
        self._file = None
    
    def at_end(self) -> None:
        super().at_end()
        self.end()


if __name__ == "__main__":
    FastFile().parse_file("examples/example1.kola")
