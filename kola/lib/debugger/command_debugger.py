from typing import Callable
from kola.lib.debugger.base import BaseDebugger


class CommandDebugger(BaseDebugger):
    """
    output the command and additional arguments to stdout
    """
    def __getitem__(self, __key: str) -> Callable[..., None]:
        if __key != "@exception":
            return lambda *args, **kwds: \
                print(f"## [DEBUG] command {__key} with args {args} kwds {kwds}")
        return super().__getitem__(__key)
