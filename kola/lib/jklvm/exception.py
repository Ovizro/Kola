from typing import Optional, Union

from kola.klvm import CommandSet
from kola.exception import KoiLangError


class JKLvmException(KoiLangError):
    """the base exception used in JKLvm"""
    __slots__ = []


class JKLvmAddressFault(JKLvmException):
    """address """
    __slots__ = ["address"]

    def __init__(self, address: int) -> None:
        super().__init__()
        self.address = address


class JKLvmExit(JKLvmException):
    """exit from an environemnt"""
    __slots__ = ["target"]
    
    def __init__(self, *args: object, target: Optional["CommandSet"] = None) -> None:
        super().__init__(*args)
        self.target = target


class JKLvmJump(JKLvmException):
    """jump to a new address"""
    __slots__ = ["target"]
    
    def __init__(self, target: Union[int, str]) -> None:
        if isinstance(target, str):
            super().__init__(f"label: {target}")
        else:
            super().__init__(f"pc+{target:08X}")
        self.target = target


class JKLvmAddressError(ValueError):
    """
    incurrect instruction address
    NOTE: This is NOT a JKLvmException
    """
    __slots__ = ["address"]

    def __init__(self, *args: object, address: Optional[int] = None) -> None:
        super().__init__(*args)
        self.address = address
