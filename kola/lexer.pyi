from typing import Any, Final


class Token:
    syn: Final[int]
    val: Final[Any]


class BaseLexer:
    filename: Final[str]
    lineno: Final[int]

    def ensure(self) -> None: ...
    def close(self) -> None: ...
    def __iter__(self) -> "BaseLexer": ...
    def __next__(self) -> Token: ...