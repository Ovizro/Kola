class KoiLangError(Exception):
    """
    Base exception for marktext compiler
    """
    __slots__ = []


class KoiLangSyntaxError(KoiLangError):
    """
    Raised when failing to parse text
    """
    __slots__ = []


class KoiLangCommandError(KoiLangError):
    """
    Raised when errors occure during executing commands
    """
    __slots__ = []