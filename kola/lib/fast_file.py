import os
from typing import Optional, Union
from typing_extensions import Literal

from ..klvm.commandset import CommandSet
from ..klvm import Environment, KoiLang, kola_command, kola_text, kola_env_enter, kola_env_exit


class FastFile(KoiLang):
    __slots__ = []

    class file(Environment):
        @kola_env_enter("file", envs="!file")
        def open(self, path: str, *, encoding: str = "utf-8") -> None:
            self.fp = open(path, "w", encoding=encoding)
        
        @kola_command
        def seek(self, __cookie: int, __whence: Union[Literal["SET", "CUR", "END"], int]) -> None:
            if __whence == "SET":
                __whence = os.SEEK_SET
            elif __whence == "CUR":
                __whence = os.SEEK_CUR
            elif __whence == "END":
                __whence = os.SEEK_END
            elif not isinstance(__whence, int):
                raise ValueError(f"invalid seek whence {__whence}")
            self.fp.seek(__cookie, __whence)
        
        @kola_text
        def text(self, text: str) -> None:
            self.fp.write(text)

        def at_finalize(self, cur_top: CommandSet) -> None:
            self.fp.close()
            return super().at_finalize(cur_top)
    
    class space(Environment):
        @kola_env_enter("space", envs="!file")
        def enter(self, name: Optional[str] = None, path: Optional[Union[str, bytes, os.PathLike]] = None) -> None:
            self.pwd = os.getcwd()
            if not path:
                assert name
                path = os.path.join(*name.split('.'))
            if not os.path.isdir(path):
                os.makedirs(path)
            os.chdir(path)
        
        @kola_env_exit("endspace")
        def exit(self) -> None:
            os.chdir(self.pwd)
        
        def at_initialize(self, cur_top: CommandSet) -> None:
            if isinstance(cur_top, FastFile.file):
                home = self.home
                cache = home.pop_start()
                home.pop_end(cache)
                # update self.back
                self.back = home.top
            return super().at_initialize(cur_top)
