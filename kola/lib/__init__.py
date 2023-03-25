import inspect
import os
import re
import sys
from glob import glob
from importlib.util import spec_from_file_location
from importlib._bootstrap import _load
from types import ModuleType
from typing import List, NamedTuple, Optional, Type

from ..klvm import CommandSetMeta, KoiLang


if "KOLA_LIB_PATH" in os.environ:
    KOLA_LIB_PATH = os.environ["KOLA_LIB_PATH"].split(os.pathsep)
else:
    KOLA_LIB_PATH = ['.', './kola_lib', os.path.dirname(__file__)]


_module_pattern = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$", re.A)


class KolaSpec(NamedTuple):
    name: str
    command_set_classes: List[CommandSetMeta]
    
    doc: Optional[str] = None
    main_class: Optional[Type[KoiLang]] = None


def collect_all() -> List[CommandSetMeta]:
    frame = inspect.currentframe()
    assert frame and frame.f_back
    return [
        i for i in frame.f_back.f_locals.values()
        if isinstance(i, CommandSetMeta)
    ]


def load_library(name: str, bases: List[str] = KOLA_LIB_PATH) -> ModuleType:
    if not _module_pattern.match(name):
        raise ValueError(f"illegal module name '{name}'")
    module_name = "kola.lib." + name
    if module_name in sys.modules:
        return sys.modules[module_name]

    for b in bases:
        spec = None
        b = os.path.abspath(b)
        full_path = os.path.join(b, name)
        if os.path.isfile(full_path):
            spec = spec_from_file_location(module_name, full_path)
        elif os.path.isdir(full_path):
            spec = spec_from_file_location(
                module_name, os.path.join(full_path, "__init__.py"),
                submodule_search_locations=[full_path]
            )
        else:
            for i in glob(full_path + '.*'):
                spec = spec_from_file_location(module_name, i)
                if spec:
                    full_path = i
                    break
        if spec:
            spec.name = module_name
            return _load(spec)
    raise ImportError(f"cannot load script {name}", name=name)


def main_class_from_module(module: ModuleType) -> Type[KoiLang]:
    spec = getattr(module, "__kola_spec__", None)
    if spec:
        if not isinstance(spec, KolaSpec):
            spec = KolaSpec(*spec)
        if spec.main_class:
            return spec.main_class
        for i in spec.command_set_classes:
            if issubclass(i, KoiLang):
                return i
    else:
        for i in module.__dict__.values():
            if isinstance(i, type) and issubclass(i, KoiLang) and i is not KoiLang:
                return i
    raise ValueError(
        f"no available main class for kola module '{spec.name if spec else module.__name__}'"
    )
