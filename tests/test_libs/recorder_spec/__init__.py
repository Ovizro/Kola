from typing import Any, Callable, Dict, NamedTuple, Tuple

from kola.klvm import KoiLang


class Instruction(NamedTuple):
    name: str
    args: Tuple[Any, ...]
    kwargs: Dict[Any, Any]


class _Recorder(KoiLang):
    __slots__ = []

    def __getitem__(self, __key: str) -> Callable[..., Instruction]:
        return lambda *args, **kwds: Instruction(__key, args, kwds)


recorder = _Recorder()


__kola_spec__ = (
    "recorder",
    [_Recorder]
)
