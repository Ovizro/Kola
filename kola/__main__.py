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

from .lexer import BaseLexer, FileLexer, StringLexer
from .exception import KoiLangError
from .lib import load_library, main_class_from_module
from .lib.debugger import KoiLangRunner, CommandDebugger

from . import __version__


def _read_stdin() -> str:
    try:
        sys.stdout.write("$kola: ")
        sys.stdout.flush()
        s = sys.stdin.readline()
        while s.endswith("\\\n"):
            sys.stdout.write("$...: ")
            sys.stdout.flush()
            s += sys.stdin.readline()
    except KeyboardInterrupt:
        sys.exit()
    return s


if __name__ == "__main__":
    parser = ArgumentParser("kola")
    parser.add_argument("file", default=None, nargs="?")
    parser.add_argument("-i", "-c", "--inline", help="parse inline string")
    parser.add_argument("-s", "--script", help="parser script")
    parser.add_argument("-d", "--debug", help="dubugger type", choices=["token", "command"])
    parser.add_argument("--encoding", help="file encoding", default="utf-8")

    namespace = parser.parse_args()

    encoding = namespace.encoding
    if namespace.file:
        lexer = FileLexer(namespace.file, encoding=encoding)
    elif namespace.inline:
        lexer = StringLexer(namespace.inline, encoding=encoding)
    elif not sys.stdin.isatty():
        lexer = BaseLexer(encoding=encoding)
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
            command_cls = CommandDebugger
            runner_type = "Command Debugger"
        elif namespace.script:
            command_cls = main_class_from_module(load_library(namespace.script))
        else:
            command_cls = KoiLangRunner

        with command_cls().exec_block() as command_set:
            if lexer:
                command_set.parse(lexer)
            else:
                print(f"KoiLang {runner_type} {__version__} on Python {sys.version}")
                while True:
                    command_set.parse(_read_stdin())
