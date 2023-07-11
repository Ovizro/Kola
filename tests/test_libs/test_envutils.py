from typing import Any, Dict, Tuple
from unittest import TestCase

from kola.klvm import AbstractHandler, Command, CommandSet, Environment, KoiLang, kola_command, kola_env_enter
from kola.klvm.commandset import CommandSet
from kola.lib.envutils import EnvRunner, WrapperEnv


RET_OBJ1 = object()
RET_OBJ2 = object()


class EnvRunnerTest(Environment):
    __slots__ = ["inited"]

    @kola_command
    def command(self) -> None:
        assert self.inited
    
    @kola_env_enter
    def enter(self) -> None:
        pass

    def set_up(self, top: CommandSet) -> None:
        super().set_up(top)
        self.inited = True
    
    def tear_down(self, top: CommandSet) -> None:
        super().tear_down(top)
        self.inited = False

    
class HandlerTest(AbstractHandler):
    __slots__ = []

    priority = 11

    def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        super().__call__(command, args, kwargs, **kwds)
        return RET_OBJ1


class Main(KoiLang):
    __slots__ = []

    class WrapperEnvTest(WrapperEnv):
        __slots__ = []

        def wrapper(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
            self.pass_down()
            return RET_OBJ2
        
        @kola_command
        def test(self) -> None:
            pass
        
        @kola_env_enter
        def enter(self) -> None:
            pass


class TestEnvUtils(TestCase):
    __slots__ = []

    def test_runner(self) -> None:
        vmobj = EnvRunner(EnvRunnerTest)
        vmobj.parse("#command")
    
    def test_wrapper(self) -> None:
        with Main().exec_block() as vmobj:
            self.assertIs(vmobj.WrapperEnvTest.enter(), RET_OBJ2)
            handler = vmobj.add_handler(HandlerTest)
            self.assertIs(vmobj.WrapperEnvTest.test(), RET_OBJ1)
        self.assertEqual(vmobj._handler, handler)
        vmobj.remove_handler(handler)
