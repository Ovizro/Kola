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
from types import ModuleType
from typing import Any, Dict, List, Optional, TypeVar, Union
from typing_extensions import Literal

from kola.exception import KoiLangCommandError
from kola.klvm import Environment, kola_command, kola_text
from kola.lib import KOLA_LIB_PATH, KolaSpec, collect_all, load_library, main_class_from_module
from kola.lib.debugger.base import BaseDebugger


T = TypeVar("T")


FLAG_DEBUG = 1


class KoiLangRunner(BaseDebugger):
    """
    default class for KoiLang module runner
    """

    var_pattern = re.compile(r"\$(\{)?(?P<name>[a-zA-Z_]\w*)(?(1)\}|)", re.ASCII)

    def __init__(self) -> None:
        super().__init__()
        self.flag = 0

    @kola_command
    def license(self) -> None:
        print(__doc__)
    
    @kola_command(alias="raise")
    def raises(self, *msg: str) -> None:
        raise KoiLangCommandError(*msg)
    
    @kola_command
    def pragma(self, *, debug: Optional[Literal["on", "off"]] = None) -> None:
        if debug:
            if debug == "on":
                self.flag |= FLAG_DEBUG
            elif debug == "off":
                self.flag &= ~FLAG_DEBUG
            else:
                raise ValueError(f"illegal value '{debug}'")
    
    @kola_command
    def echo(self, *text: str) -> None:
        print(' '.join(text))
    
    @kola_command
    def execute(self, source: str) -> None:
        code = compile(source, "<kola_runner>", "single")
        exec(code, {"kola_runner": self, "__vars__": self.vars})
    
    @kola_command(alias="export")
    def set(self, **kwds) -> None:
        self.vars.update(kwds)
    
    @kola_command
    def exit(self, code: int = 0) -> None:
        sys.exit(code)
        
    @kola_text
    def text(self, text: str) -> None:
        print(f"## [TEXT] {text}")
    
    @kola_command
    def load(self, path: Union[str, bytes, os.PathLike], type: Optional[str] = None, **kwds: Any) -> None:
        path = os.fsdecode(path)
        if type is None:
            if path.endswith(".kola"):
                type = "kola"
            else:
                type = "script"
        else:
            type = type.lower()
        if type == "kola":
            self.load_kola(path, **kwds)
        elif type in ["script", "lib"]:
            self.load_script(path, **kwds)
        else:
            raise ValueError(f"invalid type name '{type}'")
    
    @kola_command
    def load_kola(self, path: Union[str, bytes, os.PathLike], *, encoding: str = "utf-8", **kwds) -> None:
        self.parse_file(path, encoding=encoding, **kwds)
    
    @kola_command(alias=["load_lib", "load_library"])
    def load_script(self, name: str, lib_path: Optional[List[str]] = None) -> None:
        kola_module = load_library(name, lib_path or KOLA_LIB_PATH)
        self.load_command_set(kola_module)
    
    def at_start(self) -> None:
        self.vars = {}
        self.flag = 0
        self.loaded_class = set()
    
    def at_end(self) -> None:
        super().at_end()
        for i in self.loaded_class:
            i.at_end(self)
    
    def get_var(self, key: str) -> Any:
        if key == '__top__':
            return self.top.__class__.__name__
        elif key == "__dir__":
            return ', '.join(self.raw_command_set)
        elif key == "__name__":
            return self.__class__.__name__
        elif key == "__stack_info__":
            env_names = []
            top = self.top
            while top is not self:
                env_names.append(top.__class__.__name__)
                top = top.back  # type: ignore
            env_names.append("__init__")
            return " -> ".join(env_names)
        else:
            return self.vars.get(key, None)
    
    def load_command_set(self, module: ModuleType) -> None:
        cls = main_class_from_module(module)
        if self.flag & FLAG_DEBUG:
            print(f"## [DEBUG] Load class: {cls}")
        self.loaded_class.add(cls)
        cls.at_start(self)
        self.raw_command_set.update(
            cls.generate_raw_commands()
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
    
    def __kola_caller__(
            self, command: Any, args: tuple, kwargs: Dict[str, Any],
            *, bound_instance: Any = None, **kwds: Any) -> Any:
        if self.flag & FLAG_DEBUG:
            print(f"## [DEBUG] Run command: {command.__name__} ({(bound_instance or self).__class__.__name__})")
        return super().__kola_caller__(
            command,
            tuple(self.format_text(i) for i in args),
            self.format_text(kwargs),
            bound_instance=bound_instance,
            **kwds
        )
    
    def push_apply(self, __push_cache: Environment) -> None:
        if self.flag & FLAG_DEBUG:
            print(f"## [DEBUG] Push env: {__push_cache}")
        return super().push_apply(__push_cache)
    
    def pop_apply(self, __env_cache: Environment) -> None:
        if self.flag & FLAG_DEBUG:
            print(f"## [DEBUG] Pop env: {__env_cache}")
        return super().pop_apply(__env_cache)


__kola_spec__ = KolaSpec(
    "Kola Runner",
    collect_all(),
    main_class=KoiLangRunner
)
