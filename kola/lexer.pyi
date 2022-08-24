from typing import Any, Final


class Token:
    syn: Final[int]
    val: Final[Any]


class BaseLexer:
    filename: Final[str]
    lineno: Final[int]

    def ensure(self) -> None: ...
    def close(self) -> None: ...
    @property
    def _cur_text(self) -> str: ...
    def __iter__(self) -> "BaseLexer": ...
    def __next__(self) -> Token: ...


class FileLexer(BaseLexer):
    def __init__(self, filename: str) -> None: ...


class StringLexer(BaseLexer):
    content: Final[bytes]

    def __init__(self, content: str) -> None: ...