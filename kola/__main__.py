"""
Copyright 2022 Ovizro

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
import sys
from argparse import ArgumentParser
from traceback import print_exc
from typing import Callable

from .lexer import BaseLexer, FileLexer, StringLexer
from .parser import Parser
from .klvm import KoiLang, KoiLangMeta, kola_command, kola_env, kola_text
from .exception import KoiLangCommandError, KoiLangError

from . import __version__


def _load_script(path: str, encoding: str = "utf-8") -> KoiLangMeta:
    vdict = {} 
    with open(path, encoding=encoding) as f:
        exec(
            compile(f.read(), path, "exec"),
            vdict
        )
    for i in vdict.values():
        if isinstance(i, KoiLangMeta) and i is not KoiLang:
            return i
    else:
        raise TypeError("no KoiLang command set found")


class _CommandDebugger:
    def __getitem__(self, key: str) -> Callable[..., None]:
        def wrapper(*args, **kwds) -> None:
            print(f"cmd: {key} with args {args} kwds {kwds}")
        return wrapper

cmd_debugger = _CommandDebugger()


class KoiLangMain(KoiLang):
    def __init__(self) -> None:
        super().__init__()
        self.vars = {}

    @kola_command
    def version(self) -> None:
        print(__version__)
    
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
        print(self.vars.get(key, None))
    
    @kola_command
    def set(self, **kwds) -> None:
        self.vars.update(kwds)
    
    @kola_command
    def mkdir(self, dir: str, mode: int = 777) -> None:
        os.mkdir(dir, mode)
    
    @kola_env
    def open(self, path: str, mode: str = "w", *, encoding: str = "utf-8") -> None:
        if hasattr(self, "file"):
            self.file.close()
        self.file = open(path, mode, encoding=encoding)
    
    @open.exit_command
    def close(self) -> None:
        self.file.close()
        del self.file
    
    @kola_command
    def remove(self, path: str) -> None:
        os.remove(path)
    
    @kola_command(envs="__init__")
    def load(self, path: str, type: str = "kola", *, encoding: str = "utf-8") -> None:
        if type == "kola":
            self.parse_file(path)
        elif type == "script":
            cmd_set = _load_script(path, encoding=encoding)
            self.push(cmd_set.__name__, cmd_set())
        else:
            raise KoiLangCommandError("load type only supports 'kola' and 'script'")

    @kola_command
    def reset(self) -> None:
        self.command_set = self.__class__.get_command_set(self)

    @kola_text
    def text(self, text: str) -> None:
        if hasattr(self, "file"):
            self.file.write(text)
        else:
            print(f"::{text}")
    
    @kola_command
    def exit(self, code: int = 0) -> None:
        sys.exit(code)


parser = ArgumentParser("kola")
parser.add_argument("file", default=None, nargs="?")
parser.add_argument("-i", "--inline", help="parse inline string")
parser.add_argument("-s", "--script", help="parser script")
parser.add_argument("-d", "--debug", help="dubugger type", choices=["token", "command"])

namespace = parser.parse_args()


if namespace.file:
    lexer = FileLexer(namespace.file)
elif namespace.inline:
    lexer = StringLexer(namespace.inline)
else:
    lexer = None

if namespace.debug == "token":
    if lexer is None:
        print(f"KoiLang Token Debugger {__version__} on {sys.platform}")
        lexer = BaseLexer()
    while True:
        try:
            for i in lexer:
                print(i)
            break
        except KeyboardInterrupt:
            break
        except KoiLangError:
            print_exc()

elif namespace.debug == "command":
    if lexer:
        Parser(lexer, cmd_debugger).exec()
    else:
        print(f"KoiLang Command Debugger {__version__} on {sys.platform}")
        while True:
            try:
                sys.stdout.write("$kola: ")
                sys.stdout.flush()
                i = sys.stdin.readline()
                while i.endswith("\\\n"):
                    sys.stdout.write("$...: ")
                    sys.stdout.flush()
                    i += sys.stdin.readline()
                Parser(StringLexer(i), cmd_debugger).exec_once()
            except KeyboardInterrupt:
                break
            except KoiLangError:
                print_exc()
    
else:
    if namespace.script:
        command_cls = _load_script(namespace.script)
    else:
        command_cls = KoiLangMain

    command_set = command_cls()
    if lexer:
        command_set.parse(lexer)
    else:
        print(f"KoiLang Runner {__version__} on {sys.platform}")
        while True:
            try:
                sys.stdout.write("$kola: ")
                sys.stdout.flush()
                i = sys.stdin.readline()
                while i.endswith("\\\n"):
                    sys.stdout.write("$... : ")
                    sys.stdout.flush()
                    i += sys.stdin.readline()
                command_set.parse(i)
            except KeyboardInterrupt:
                break
            except KoiLangError:
                print_exc()
    