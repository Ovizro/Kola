from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Type, Union


from .commandset import CommandSet


class Mask(ABC):
    __slots__ = ["type", "not_"]

    class MType(Enum):
        default = ""    # test all reachable env
        exact = "+"     # test top env
        all = "*"      # test all env

    def __init__(self, type: Union[MType, str] = MType.default, not_: bool = False) -> None:
        if isinstance(type, str):
            type = self.MType(type)
        self.type = type
        self.not_ = not_

    @abstractmethod
    def __contains__(self, other: Any) -> bool:
        raise NotImplementedError


class ClassTypeMask(Mask):
    __slots__ = ["env_type"]

    def __init__(
        self,
        env_type: Type[CommandSet],
        type: Union[Mask.MType, str] = Mask.MType.default,
        not_: bool = False
    ) -> None:
        self.env_type = env_type
        super().__init__(type=type, not_=not_)
    
    def __contains__(self, other: Any) -> bool:
        return isinstance(other, self.env_type)


class ClassNameMask(Mask):
    __slots__ = ["env_name"]

    def __init__(
        self,
        env_name: str,
        type: Union[Mask.MType, str, None] = None,
        not_: bool = False,
        **kwds: CommandSet
    ) -> None:
        if env_name.startswith('!'):
            env_name = env_name[1:]
            not_ = True
        if type is None:
            if env_name.startswith('+'):
                env_name = env_name[1:]
                type = Mask.MType.exact
            elif env_name.startswith('*'):
                env_name = env_name[1:]
                type = Mask.MType.all
            else:
                type = Mask.MType.default
        elif env_name[0] in ('+', '*'):
            raise ValueError(
                "the name prefix should not be used to specify the type when the Mask type is specified"
            )
        if env_name.startswith('$'):
            name = env_name[1:]
            if name in kwds:
                env_name = kwds[name].__class__.__name__
        elif env_name == "__init__":
            env_name = kwds["__init__"].__class__.__name__
        self.env_name = env_name
        super().__init__(type=type, not_=not_)
    
    def __contains__(self, other: Any) -> bool:
        return self.env_name == other.__class__.__name__
