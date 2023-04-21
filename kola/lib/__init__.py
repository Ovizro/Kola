"""
Kola sub libraries support modules

Include some useful builtin kola sub module.
And modules imported from `load_library()` will be mounted as a sub module.
"""

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


if "KOLA_LIB_PATH" in os.environ:  # pragma: no cover
    KOLA_LIB_PATH = os.environ["KOLA_LIB_PATH"].split(os.pathsep)
else:
    KOLA_LIB_PATH = ['.', './kola_lib', os.path.dirname(__file__)]


_module_pattern = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$", re.A)


class KolaSpec(NamedTuple):
    """
    Kola module spec
    
    Usage:
        __kola_spec__ = KolaSpec(
            __name__,
            collect_all()
        )
    """
    name: str
    command_set_classes: List[CommandSetMeta]
    
    doc: Optional[str] = None
    main_class: Optional[Type[KoiLang]] = None


def collect_all() -> List[CommandSetMeta]:
    """get all CommandSet class defined in the module

    :return: a list of CommandSet class found
    :rtype: List[CommandSetMeta]
    """
    frame = inspect.currentframe()
    if not frame or not frame.f_back:  # pragma: no cover
        raise ValueError("cannot read variables from the frame")
    return [
        i for i in frame.f_back.f_locals.values()
        if isinstance(i, CommandSetMeta)
    ]


def load_library(name: str, paths: List[str] = KOLA_LIB_PATH) -> ModuleType:
    """load a Phython script or package as a Kola module

    :param name: module name like 'mymodule.sub'
    :type name: str
    :param paths: base path to load the module, defaults to KOLA_LIB_PATH
    :type paths: List[str], optional
    :raises ValueError: illegal module name
    :raises ImportError: fail to load the module
    :return: the Kola module
    :rtype: ModuleType
    """
    if not _module_pattern.match(name):  # pragma: no cover
        raise ValueError(f"illegal module name '{name}'")
    module_name = "kola.lib." + name
    if module_name in sys.modules:
        return sys.modules[module_name]

    for b in paths:
        spec = None
        b = os.path.abspath(b)
        full_path = os.path.join(b, name)
        if os.path.isdir(full_path):
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
    raise ImportError(f"cannot load script {name}", name=name)  # pragma: no cover


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
    raise ValueError(  # pragma: no cover
        f"no available main class for kola module '{spec.name if spec else module.__name__}'"
    )
