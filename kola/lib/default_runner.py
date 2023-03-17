"""
Copyright 2023 Ovizro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import re
import sys
from importlib import import_module
from typing import Any, Dict, Optional, TypeVar, Union

from .. import __version__
from ..exception import KoiLangCommandError
from ..klvm import KoiLang, kola_command, kola_text
from . import KOLA_LIB_PATH


T = TypeVar("T")


class KoiLangRunner(KoiLang):
    """
    default class for KoiLang module runner
    """
    __slots__ = ["vars"]

    var_pattern = re.compile(r"\$(\{)?(?P<name>[a-zA-Z_]\w*)(?(1)\}|)", re.ASCII)

    @kola_command
    def version(self, __chk_ver: Optional[int] = None) -> None:
        if __chk_ver is None:
            print(__version__)
        elif __chk_ver != 100:
            print(f"version {__chk_ver} is not support by runner {__version__}")
            sys.exit(2)
    
    @kola_command
    def license(self) -> None:
        print(__doc__)
    
    @kola_command
    def raises(self) -> None:
        raise KoiLangCommandError
    
    @kola_command
    def echo(self, *text: str) -> None:
        print(' '.join(text))
    
    @kola_command("get")
    def get_(self, key: str) -> None:
        print(self.get_var(key))
    
    @kola_command
    def set(self, **kwds) -> None:
        self.vars.update(kwds)
    
    @kola_command
    def exit(self, code: int = 0) -> None:
        sys.exit(code)
        
    @kola_text
    def text(self, text: str) -> None:
        print(f"::{text}")
    
    @kola_command
    def load(self, path: Union[str, bytes, os.PathLike], type: str = "kola", **kwds: Any) -> None:
        type = type.lower()
        if type == "kola":
            self.load_kola(path, **kwds)
        elif type == "script":
            self.load_script(path, **kwds)
        elif type in {"lib", "library"}:
            self.load_lib(path, **kwds)
        else:
            raise ValueError(f"invalid type name '{type}'")
    
    @kola_command
    def load_kola(self, path: Union[str, bytes, os.PathLike], *, encoding: str = "utf-8", **kwds) -> None:
        self.parse_file(path, encoding=encoding, **kwds)
    
    @kola_command
    def load_script(self, path: Union[str, bytes, os.PathLike], *, encoding: str = "utf-8") -> None:
        vdict = {}
        with open(path, encoding=encoding) as f:
            exec(
                compile(f.read(), path, "exec"),
                vdict
            )
        self.load_command_set(vdict)
    
    @kola_command(alias="load_library")
    def load_lib(self, name: str, *, encoding: str = "utf-8") -> None:
        try:
            module = import_module(f"kola.lib.{name}", "kola.lib")
            self.load_command_set(module.__dict__)
            return
        except ImportError:
            pass
        self.load_script(
            os.path.join(KOLA_LIB_PATH, f"{name}.py"), encoding=encoding
        )
    
    def at_start(self) -> None:
        self.vars = {}
    
    def get_var(self, key: str) -> Any:
        if key == '__top__':
            return self.top.__class__.__name__
        elif key == "__dir__":
            return ', '.join(self.raw_command_set)
        elif key == "__name__":
            return self.__class__.__name__
        else:
            return self.vars.get(key, None)
    
    def load_command_set(self, vdict: Dict[str, Any]) -> None:
        for i in vdict.values():
            if issubclass(i, KoiLang) and i is not KoiLang:
                break
        else:
            raise TypeError("the KoiLang main class unfound")
        self.raw_command_set.update(
            i.generate_raw_commands()
        )
    
    def format_text(self, argument: T) -> T:
        if isinstance(argument, list):
            return [self.format_text(i) for i in argument]  # type: ignore
        elif isinstance(argument, dict):
            return {k: self.format_text(v) for k, v in argument.items()}  # type: ignore
        elif isinstance(argument, str):
            return self.var_pattern.sub(
                lambda match: str(self.get_var(match.group("name")) or ''),
                argument
            )
        return argument
    
    def __kola_caller__(self, command: Any, args: tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        return super().__kola_caller__(
            command,
            tuple(self.format_text(i) for i in args),
            self.format_text(kwargs),
            **kwds
        )
