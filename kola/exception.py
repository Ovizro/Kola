class KoiLangError(Exception):
    """
    base exception for marktext compiler
    """
    __slots__ = []


class KoiLangSyntaxError(KoiLangError):
    """
    failed to parse text
    """
    __slots__ = []


class KoiLangCommandError(KoiLangError):
    """
    errors occurred during executing commands
    """
    __slots__ = []


class KoiLangCommandNotFoundError(KoiLangCommandError):
    """
    failed to fetch the command in the command set
    """
    __slots__ = []
