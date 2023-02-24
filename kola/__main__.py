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
from io import StringIO
import os
import sys
from argparse import ArgumentParser
from traceback import print_exc
from typing import Any, Callable, Optional

from .lexer import BaseLexer, FileLexer, StringLexer
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


class _CommandDebugger(KoiLang):
    def __getitem__(self, key: str) -> Callable[..., None]:
        def wrapper(*args, **kwds) -> None:
            print(f"cmd: {key} with args {args} kwds {kwds}")
        return wrapper


class KoiLangMain(KoiLang):
    def __init__(self, parent: Optional[KoiLang] = None) -> None:
        super().__init__(parent)
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
        print(self.get_var(key))
    
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
    
    @kola_command
    def load(self, path: str, type: str = "kola", *, encoding: str = "utf-8") -> None:
        if type == "kola":
            self.parse_file(path)
        elif type == "script":
            cmd_set = _load_script(path, encoding=encoding)
            self.push(cmd_set.__name__, cmd_set())
        else:
            raise ValueError("load type only supports 'kola' and 'script'")

    @kola_command
    def reset(self) -> None:
        while self._stack.name != "__init__":
            self.pop()
            
    @kola_text
    def text(self, text: str) -> None:
        s = StringIO()
        i = 0
        while i < len(text):
            if text[i] == '$':
                i += 1
                j = i
                while text[i] not in ['\n', ' ', '\t']:
                    i += 1
                    if i >= len(text):
                        break
                key = text[j: i]
                val = self.get_var(key) or ''
                s.write(str(val))
            else:
                s.write(text[i])
                i += 1
        text = s.getvalue()
        if hasattr(self, "file"):
            self.file.write(text)
        else:
            print(f"::{text}")
    
    @kola_command
    def exit(self, code: int = 0) -> None:
        sys.exit(code)
    
    def get_var(self, key: str) -> Any:
        if key == "__name__":
            return self.__class__.__name__
        elif key == '__top__':
            return self.top[0]
        elif key == "__dir__":
            return ', '.join(i.__name__ for i in self.__class__.__command_field__)
        else:
            return self.vars.get(key, None)


def _read_stdin() -> str:
    sys.stdout.write("$kola: ")
    sys.stdout.flush()
    s = sys.stdin.readline()
    while s.endswith("\\\n"):
        sys.stdout.write("$...: ")
        sys.stdout.flush()
        s += sys.stdin.readline()
    return s


if __name__ == "__main__":
    parser = ArgumentParser("kola")
    parser.add_argument("file", default=None, nargs="?")
    parser.add_argument("-i", "--inline", help="parse inline string")
    parser.add_argument("-s", "--script", help="parser script")
    parser.add_argument("-d", "--debug", help="dubugger type", choices=["token", "command"])
    parser.add_argument("--encoding", help="file encoding", default="utf-8")

    namespace = parser.parse_args()

    if namespace.file:
        lexer = FileLexer(namespace.file)
    elif namespace.inline:
        lexer = StringLexer(namespace.inline)
    else:
        lexer = None

    runner_type = "Runner"
    if namespace.debug == "token":
        runner_type = "Token Debugger"
        if lexer is None:
            print(f"KoiLang {runner_type} {__version__} on Python {sys.version}")
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
    else:
        if namespace.debug == "command":
            command_cls = _CommandDebugger
            runner_type = "Command Debugger"
        elif namespace.script:
            command_cls = _load_script(namespace.script)
        else:
            command_cls = KoiLangMain

        command_set = command_cls()
        if lexer:
            command_set.parse(lexer)
        else:
            print(f"KoiLang {runner_type} {__version__} on Python {sys.version}")
            while True:
                try:
                    command_set.parse(_read_stdin())
                except KeyboardInterrupt:
                    break
                except KoiLangError:
                    print_exc()
