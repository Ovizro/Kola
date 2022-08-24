from typing import Callable


class CommandTest:
    def __class_getitem__(cls, key: str) -> Callable[..., None]:
        def wrapper(*args, **kwds) -> None:
            print(f"cmd: {key} with args {args} kwds {kwds}")
        return wrapper
