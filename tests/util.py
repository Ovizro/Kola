from typing import Any, Callable, Dict, Tuple


class _CommandTest:
    def __getitem__(self, key: str) -> Callable[..., Tuple[str, tuple, Dict[str, Any]]]:
        def wrapper(*args, **kwds) -> Tuple[str, tuple, Dict[str, Any]]:
            return key, args, kwds
        return wrapper

cmd_test = _CommandTest()