import os
from shutil import copy
from unittest import TestCase, skipUnless

from kola.lib import KOLA_LIB_PATH, load_library, main_class_from_module

try:
    from pyximport.pyxbuild import pyx_to_dll
    from pyximport.pyximport import get_distutils_extension
except ImportError:  # pragma: no cover
    pyx_to_dll = None


base_path = os.path.dirname(__file__)


class TestLibImport(TestCase):
    def test_lib(self) -> None:
        KOLA_LIB_PATH.append(base_path)
        recorder = load_library("recorder")

        recorder = load_library("recorder_test")
        main = main_class_from_module(recorder)
        from kola.lib.recorder_test import _Recorder  # type: ignore
        self.assertIs(main, _Recorder)
        
        recorder = load_library("_recorder_spec")
        main = main_class_from_module(recorder)
        from kola.lib._recorder_spec import _Recorder  # type: ignore
        self.assertIs(main, _Recorder)

    @skipUnless(pyx_to_dll, "Cython module is not available")
    def test_binlib(self) -> None:
        assert pyx_to_dll
        bin_name = "recorder_bin"
        bin_path = bin_name + ".pyx"
        copy(os.path.join(base_path, "recorder_test.py"), bin_path)
        self.addCleanup(lambda: [os.remove(bin_name + prefix) for prefix in [".c", ".pyx"]])
        ext, setup_args = get_distutils_extension(bin_name, bin_path, "3")
        pyx_to_dll(
            bin_path,
            ext,
            inplace=True,
            pyxbuild_dir="build",
            setup_args=setup_args,
        )
        recorder = load_library(bin_name)
        main = main_class_from_module(recorder)
        from kola.lib.recorder_bin import _Recorder  # type: ignore
        self.assertIs(main, _Recorder)

        debugger = load_library("debugger")
        main = main_class_from_module(debugger)
        from kola.lib.debugger import KoiLangRunner
        self.assertIs(main, KoiLangRunner)
