import os
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, Union, overload

from kola.lexer import BaseLexer, FileLexer, StringLexer
from kola.parser import Parser
from kola.klvm import CommandSet


class Instruction(NamedTuple):
    name: str
    args: Tuple[Any, ...]
    kwargs: Dict[Any, Any]


class _Recorder(CommandSet):
    __slots__ = []

    def __getitem__(self, __key: str) -> Callable[..., Instruction]:
        return lambda *args, **kwds: Instruction(__key, args, kwds)


recorder = _Recorder()


@overload
def parse(__lexer: BaseLexer) -> List[Instruction]: ...
@overload
def parse(__str: str, *, command_threshold: int = 1, no_lstrip: bool = ...) -> List[Instruction]: ...
def parse(__lexer_or_str: Union[str, BaseLexer], **kwds: Any) -> List[Instruction]:  # noqa: E302
    if isinstance(__lexer_or_str, str):
        __lexer_or_str = StringLexer(__lexer_or_str, **kwds)
    else:
        assert not kwds
    return list(Parser(__lexer_or_str, recorder))


def parse_file(path: Union[str, bytes, os.PathLike], *, encoding: Optional[str] = None, **kwds: Any) -> List[Instruction]:
    lexer = FileLexer(path, encoding=encoding or "utf-8", **kwds)
    return parse(lexer)
