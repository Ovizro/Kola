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
S_ANNOTATION: int


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
    def __init__(self, *, encoding: str = ..., command_threshold: int = 1) -> None: ...
    def close(self) -> None: ...
    @property
    def filename(self) -> str: ...
    @property
    def lineno(self) -> int: ...
    @property
    def column(self) -> int: ...
    @property
    def command_threshold(self) -> int: ...
    @property
    def closed(self) -> bool: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> Token: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args) -> None: ...


class FileLexer(BaseLexer):
    def __init__(self, __path: Union[str, bytes, os.PathLike], *, encoding: str = ...,
                 command_threshold: int = 1) -> None: ...
    @property
    def filename(self) -> Union[str, bytes, os.PathLike]: ...


class StringLexer(BaseLexer):
    content: Final[bytes]

    def __init__(self, content: Union[str, bytes], *, encoding: str = ...,
                 command_threshold: int = 1) -> None: ...
