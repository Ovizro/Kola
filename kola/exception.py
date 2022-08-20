from traceback import format_tb


class KoiLangError(Exception):
    """
    Base exception for marktext compiler
    """
    __slots__ = []


class KoiLangCompileError(Exception):
    """
    Raised when the compiler fail to parse text
    """


class KoiLangCommandError(Exception):
    """
    Raised when errors occure during executing commands
    """
    __slots__ = ["exc_obj"]

    def __init__(self, msg: str, **exc_obj: Exception) -> None:
        self.exc_obj = exc_obj
        super().__init__(msg)
    
    def __str__(self) -> str:
        msg = super().__str__()
        for name, exc in self.exc_obj.items():

            msg += f"\n  - {exc.__class__.__name__}: {exc}"
        return msg