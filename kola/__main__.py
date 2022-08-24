import sys
from argparse import ArgumentParser

from . import BaseLexer, FileLexer, StringLexer, __version__

parser = ArgumentParser("kola")
parser.add_argument("file", default=None, nargs="?")
parser.add_argument("-i", "--inline", help="parse inline string")
parser.add_argument("-p", "--parser", help="parser script")
parser.add_argument("-t", "--token", action="store_true", help="token dubugger")

namespace = parser.parse_args()

if namespace.file:
    lexer = FileLexer(namespace.file)
elif namespace.inline:
    lexer = StringLexer(namespace.inline)
else:
    lexer = BaseLexer()

print(f"KoiLang Token Debugger {__version__} in file \"{lexer.filename}\" on {sys.platform}")
for i in lexer:
    print(i)