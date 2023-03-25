"""
Kola builtin debugger module
"""

from kola.lib import KolaSpec, collect_all
from .base import BaseDebugger
from .command_debugger import CommandDebugger
from .default_runner import KoiLangRunner


__kola_spec__ = KolaSpec(
    "debugger",
    collect_all(),
    main_class=KoiLangRunner,
    doc=__doc__
)
