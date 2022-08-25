import sys
from argparse import ArgumentParser
from typing import Any, Callable, Dict, Tuple

from . import BaseLexer, FileLexer, StringLexer, Parser, __version__


class CommandDebugger:
    def __class_getitem__(cls, key: str) -> Callable[..., None]:
        def wrapper(*args, **kwds) -> None:
            print(f"cmd: {key} with args {args} kwds {kwds}")
        return wrapper


parser = ArgumentParser("kola")
parser.add_argument("file", default=None, nargs="?")
parser.add_argument("-i", "--inline", help="parse inline string")
parser.add_argument("-p", "--parser", help="parser script")
parser.add_argument("-d", "--debug", help="dubugger type", choices=["token", "grammar"])

namespace = parser.parse_args()

if namespace.file:
    lexer = FileLexer(namespace.file)
elif namespace.inline:
    lexer = StringLexer(namespace.inline)
else:
    lexer = BaseLexer()

if namespace.debug == "token":
    print(f"KoiLang Token Debugger {__version__} in file \"{lexer.filename}\" on {sys.platform}")
    for i in lexer:
        print(i)
elif namespace.debug == "grammar":
    print(f"KoiLang Grammar Debugger {__version__} in file \"{lexer.filename}\" on {sys.platform}")
    Parser(lexer, CommandDebugger).exec_() # type: ignore
