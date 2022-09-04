from typing import Any, Final


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


class Token:
    syn: Final[int]
    val: Final[Any]

    def get_flag(self) -> int: ...


class BaseLexer:
    filename: Final[str]
    lineno: Final[int]
    stat: Final[int]

    def __init__(self, *, stat: int = 0) -> None: ...
    def ensure(self) -> None: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    @property
    def _cur_text(self) -> str: ...
    def __iter__(self) -> "BaseLexer": ...
    def __next__(self) -> Token: ...


class FileLexer(BaseLexer):
    def __init__(self, filename: str, *, stat: int = 0) -> None: ...


class StringLexer(BaseLexer):
    content: Final[bytes]

    def __init__(self, content: str, *, stat: int = 0) -> None: ...