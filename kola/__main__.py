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
import sys
from argparse import ArgumentParser
from traceback import print_exc
from typing import Any, Callable, Dict, Tuple

from .lexer import BaseLexer, FileLexer, StringLexer
from .parser import Parser
from .klvm import KoiLang, KoiLangMeta, kola_command, kola_number, kola_text
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


class CommandDebugger:
    def __class_getitem__(cls, key: str) -> Callable[..., None]:
        def wrapper(*args, **kwds) -> None:
            print(f"cmd: {key} with args {args} kwds {kwds}")
        return wrapper


class KoiLangMain(KoiLang):
    def __init__(self) -> None:
        self.vars = {}
        super().__init__()

    @kola_command
    def version(self) -> None:
        print(__version__)
    
    @kola_command
    def author(self, author: str = "name") -> None:
        if author == "name":
            print("Ovizro")
        elif author == "email":
            print("Ovizro@hypercol.com")
        else:
            raise KoiLangCommandError("author information only supports 'name' and 'email'")

    @kola_command
    def license(self) -> None:
        print(__doc__)
    
    @kola_command
    def raises(self) -> None:
        raise KoiLangCommandError
    
    @kola_command
    def echo(self, text: str) -> None:
        print(text)
    
    @kola_command
    def get(self, key: str) -> None:
        print(self.vars.get(key, None))
    
    @kola_command
    def set(self, **kwds) -> None:
        self.vars.update(kwds)
    
    @kola_command
    def load(self, path: str, type: str = "kola", *, encoding: str = "utf-8") -> None:
        if type == "kola":
            self.parse_file(path)
        elif type == "script":
            cmd_set = _load_script(path, encoding=encoding)()
            self.command_set.update(cmd_set.command_set)
        else:
            raise KoiLangCommandError("load type only supports 'kola' and 'script'")

    @kola_text
    def text(self, text: str) -> None:
        print(f"::{text}")
    
    @kola_command
    def exit(self, code: int = 0) -> None:
        sys.exit(code)


parser = ArgumentParser("kola")
parser.add_argument("file", default=None, nargs="?")
parser.add_argument("-i", "--inline", help="parse inline string")
parser.add_argument("-s", "--script", help="parser script")
parser.add_argument("-d", "--debug", help="dubugger type", choices=["token", "grammar"])

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
            print_exc(5)

elif namespace.debug == "grammar":
    if lexer:
        Parser(lexer, CommandDebugger).exec_()
    else:
        print(f"KoiLang Grammar Debugger {__version__} on {sys.platform}")
        while True:
            try:
                sys.stdout.write("$kola: ")
                sys.stdout.flush()
                i = sys.stdin.readline()
                while i.endswith("\\\n"):
                    sys.stdout.write("... :")
                    sys.stdout.flush()
                    i += sys.stdin.readline()
                Parser(StringLexer(i), CommandDebugger).exec_once()
            except KeyboardInterrupt:
                break
            except KoiLangError:
                print_exc(5)
    
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
                    sys.stdout.write("... :")
                    sys.stdout.flush()
                    i += sys.stdin.readline()
                command_set.parse(i)
            except KeyboardInterrupt:
                break
            except KoiLangError:
                print_exc(5)
    