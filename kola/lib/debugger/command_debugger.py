from typing import Callable
from kola.lib.debugger.base import BaseDebugger


class CommandDebugger(BaseDebugger):
    def __getitem__(self, __key: str) -> Callable[..., None]:
        return lambda *args, **kwds: \
            print(f"## [DEBUG] command {__key} with args {args} kwds {kwds}")
