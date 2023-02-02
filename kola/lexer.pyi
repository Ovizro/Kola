import os
from typing import Any, Final, Union, final
from typing_extensions import Self


S_CMD: int
S_CMD_N: int
S_TEXT: int
S_LITERAL: int
S_STRING: int
S_NUM: int
S_NUM_H: int
S_NUM_B: int
S_NUM_F: int
S_CLN: int
S_CMA: int
S_SLP: int
S_SRP: int


@final
class Token:
    """
    Token used in lexer

    Don't instantiate this class directly unless you make
    sure enough arguments provided.
    """

    syn: Final[int]
    val: Final[Any]

    def __new__(cls, syn: int, val: Any = ..., *, lineno: int = ..., raw_val: bytes = ...) -> Self: ...
    def get_flag(self) -> int: ...


class BaseLexer:
    lineno: Final[int]
    stat: Final[int]

    def __init__(self, *, encoding: str = ..., stat: int = 0) -> None: ...
    def close(self) -> None: ...
    @property
    def filename(self) -> str: ...
    @property
    def closed(self) -> bool: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> Token: ...


class FileLexer(BaseLexer):
    def __init__(self, __path: Union[str, bytes, os.PathLike], *, encoding: str = ..., stat: int = 0) -> None: ...
    @property
    def filename(self) -> Union[str, bytes, os.PathLike]: ...


class StringLexer(BaseLexer):
    content: Final[bytes]

    def __init__(self, content: Union[str, bytes], *, encoding: str = ..., stat: int = 0) -> None: ...
