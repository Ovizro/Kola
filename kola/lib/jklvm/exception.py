from typing import Optional

from kola.exception import KoiLangError


class JKLvmException(KoiLangError):
    """the base exception used in JKLvm"""
    __slots__ = []


class JKLvmExit(JKLvmException):
    """exit from an environemnt"""
    __slots__ = []


class JKLvmJump(JKLvmException):
    """jump to a new address"""
    __slots__ = ["addr"]
    
    def __init__(self, __addr: int) -> None:
        super().__init__(format(__addr, "08X"))
        self.addr = __addr


class JKLvmAddressError(ValueError):
    """
    incurrect instruction address
    NOTE: This is NOT a JKLvmException
    """
    __slots__ = ["address"]

    def __init__(self, *args: object, address: Optional[int] = None) -> None:
        super().__init__(*args)
        self.address = address
