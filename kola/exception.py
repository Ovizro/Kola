from traceback import format_tb


class KoiLangError(Exception):
    """
    Base exception for marktext compiler
    """
    __slots__ = []


class KoiLangSyntaxError(Exception):
    """
    Raised when failing to parse text
    """
    __slots__ = ["err_code"]

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.err_code = 0


class KoiLangCommandError(Exception):
    """
    Raised when errors occure during executing commands
    """
    __slots__ = []