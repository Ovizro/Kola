import os
from pathlib import Path
from typing import ClassVar, Optional, Type, Union
from typing_extensions import Literal

from kola.klvm import CommandSet, Environment, KoiLang, kola_command, kola_text, kola_env_enter, kola_env_exit
from kola.lib import _module_pattern


class FastFiles(KoiLang):
    __slots__ = ["base_path", "__base_path"]

    def __init__(self, base: Union[str, os.PathLike, None] = None) -> None:
        super().__init__()
        if base is None:
            self.__base_path = Path.cwd()
        else:
            self.__base_path = Path(base)

    class FileContains(Environment):
        __slots__ = ["fp"]

        home: "FastFiles"
        Space: ClassVar[Type["FastFiles.Space"]]

        @kola_env_enter("file", envs="!$?")
        def open(self, path: Union[str, os.PathLike], *, encoding: str = "utf-8") -> None:
            base = self.home.base_path
            self.fp = (base / path).open("w", encoding=encoding)
        
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
        
        @property
        def path(self) -> str:
            return self.fp.name

        def tear_down(self, top: CommandSet) -> None:
            self.fp.close()
            return super().tear_down(top)
    
    class Space(Environment):
        __slots__ = ["parent_path", "path"]

        home: "FastFiles"
        FileContains: ClassVar[Type["FastFiles.FileContains"]]

        @kola_env_enter("space")
        def enter(self, name: Optional[str] = None, path: Optional[Union[str, os.PathLike]] = None) -> None:
            base_path = self.home.base_path
            self.parent_path = base_path
            if not path:
                assert name
                if not _module_pattern.match(name):
                    raise ValueError(f"invalid space name {name}")
                path = os.path.join(*name.split('.'))
            self.path = base_path / path
            self.path.mkdir(755, exist_ok=True)
            self.home.base_path = self.path
        
        @kola_env_exit("endspace")
        def exit(self) -> None:
            self.home.base_path = self.parent_path
        
        def set_up(self, top: CommandSet) -> None:
            if isinstance(top, FastFiles.FileContains):
                home = self.home
                cache = home.pop_prepare()
                home.pop_apply(cache)
                # update self.back
                self.back = home.top
            return super().set_up(top)
    
    def at_start(self) -> None:
        self.base_path = self.__base_path
    
    def at_end(self) -> None:
        del self.base_path


FastFiles.FileContains.Space = FastFiles.Space
FastFiles.Space.FileContains = FastFiles.FileContains
