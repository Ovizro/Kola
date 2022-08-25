from typing import Any, Callable, Dict, Tuple


class CommandTest:
    def __class_getitem__(cls, key: str) -> Callable[..., Tuple[str, tuple, Dict[str, Any]]]:
        def wrapper(*args, **kwds) -> Tuple[str, tuple, Dict[str, Any]]:
            return key, args, kwds
        return wrapper