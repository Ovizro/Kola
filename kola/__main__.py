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
from typing import Callable, Type

from .lexer import BaseLexer, FileLexer, StringLexer
from .klvm import KoiLang
from .exception import KoiLangError
from .lib.default_runner import KoiLangRunner

from . import __version__


def _load_script(path: str, encoding: str = "utf-8") -> Type[KoiLang]:
    vdict = {}
    with open(path, encoding=encoding) as f:
        exec(
            compile(f.read(), path, "exec"),
            vdict
        )
    for i in vdict.values():
        if issubclass(i, KoiLang) and i is not KoiLang:
            return i
    else:
        raise TypeError("no KoiLang command set found")


class _CommandDebugger(KoiLang):
    def __getitem__(self, key: str) -> Callable[..., None]:
        return lambda *args, **kwds: print(f"cmd: {key} with args {args} kwds {kwds}")


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
            command_cls = KoiLangRunner

        command_set = command_cls()
        with command_set.exec_block():
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
