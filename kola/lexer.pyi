import os
from typing import Any, ClassVar, Final, FrozenSet, Union, final, TypedDict
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
F_DISABLED: int
F_LSTRIP_TEXT: int


class _LexerData(TypedDict):
    filename: str
    encoding: str
    command_threshold: int
    flag: int


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


class LexerConfig:
    """
    Python-level interface to access extra lexer data
    """
    data_names: ClassVar[FrozenSet[str]]

    def __init__(self, lexer: BaseLexer) -> None: ...
    def dict(self) -> _LexerData: ...
    def set(
        self,
        *,
        encoding: str = ...,
        command_threshold: int = ...,
        flag: int = ...,
        disabled: bool = ...,
        no_lstrip: bool = ...
    ) -> None: ...
    @property
    def filename(self) -> str: ...
    @property
    def encoding(self) -> str: ...
    @encoding.setter
    def encoding(self, val: str) -> None: ...
    @property
    def command_threshold(self) -> int: ...
    @command_threshold.setter
    def command_threshold(self, cmd_threshold: int) -> None: ...    
    @property
    def flag(self) -> int: ...
    @flag.setter
    def flag(self, val: int) -> None: ...
    @property
    def disabled(self) -> bool: ...
    @disabled.setter
    def disabled(self, val: bool) -> None: ...
    @property
    def no_lstrip(self) -> bool: ...
    @no_lstrip.setter
    def no_lstrip(self, val: bool) -> None: ...


class BaseLexer:
    def __init__(self, *, encoding: str = ..., command_threshold: int = 1, no_lstrip: bool = ...) -> None: ...
    def close(self) -> None: ...
    @property
    def filename(self) -> str: ...
    @property
    def lineno(self) -> int: ...
    @property
    def column(self) -> int: ...
    @property
    def config(self) -> LexerConfig: ...
    @property
    def closed(self) -> bool: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> Token: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args) -> None: ...


class FileLexer(BaseLexer):
    def __init__(self, __path: Union[str, bytes, os.PathLike], *, encoding: str = ...,
                 command_threshold: int = 1, no_lstrip: bool = ...) -> None: ...
    @property
    def filename(self) -> Union[str, bytes, os.PathLike]: ...


class StringLexer(BaseLexer):
    content: Final[bytes]

    def __init__(self, content: Union[str, bytes], *, encoding: str = ...,
                 command_threshold: int = 1, no_lstrip: bool = ...) -> None: ...
