from abc import abstractmethod
from inspect import currentframe
from typing import Any, ClassVar, Dict, Optional, Tuple, Type, Union

from kola.klvm import Command, CommandSet, Environment, KoiLang, AbstractHandler
from kola.klvm.command import Command
from kola.klvm.commandset import CommandSet
from kola.klvm.environment import EnvironmentAutopop


class EnvRunner(KoiLang):
    __slots__ = ["env_class"]

    def __init__(self, env_class: Type[Environment]) -> None:
        super().__init__()
        self.env_class = env_class
    
    def at_start(self) -> None:
        if self.top is self:
            self.push_apply(self.push_prepare(self.env_class))
    

class HandlerEnv(Environment):
    __slots__ = ["_handler"]

    Handler: ClassVar = AbstractHandler

    def __init__(self, back: CommandSet) -> None:
        super(Environment, self).__init__()
        self.back = back

        if self.__class__.__env_autopop__:
            # for these have no exit point, use the same name as entry points
            for c in self.__class__.__env_entry__:
                self.raw_command_set.update(
                    EnvironmentAutopop.from_command(c).__kola_command__()
                )

    def set_up(self, top: CommandSet) -> None:
        self._handler = self.home.add_handler(self.__class__.Handler(self))  # type: ignore
        super().set_up(top)
    
    def tear_down(self, top: CommandSet) -> None:
        super().tear_down(top)
        self.home.remove_handler(self._handler)
        del self._handler


class WrapperEnv(HandlerEnv):
    __slots__ = []
    
    @abstractmethod
    def wrapper(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
        return self.pass_down()
    
    def pass_down(
        self,
        command: Union[Command, None] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        **kwds: Any
    ) -> Any:
        frame = currentframe()
        assert frame and frame.f_back, "failed to fetch frames"
        frame = frame.f_back
        try:
            assert frame.f_locals["self"] is self
            command = command or frame.f_locals["command"]
            args = args or frame.f_locals["args"]
            kwargs = kwargs or frame.f_locals["kwargs"]
            if not kwds:
                kwds.update(frame.f_locals["kwds"])
        except Exception as e:
            raise RuntimeError("failed to fetch arguments") from e
        handler_frame = frame.f_back
        assert handler_frame
        try:
            handler: WrapperEnv.Handler = handler_frame.f_locals["self"]
        except Exception as e:
            raise RuntimeError("Incorrect handler object call stack frame") from e
        return super(handler.__class__, handler).__call__(command, args, kwargs, **kwds)

    class Handler(AbstractHandler):
        __slots__ = []

        priority = 1
        owner: "WrapperEnv"

        def __call__(self, command: Command, args: Tuple, kwargs: Dict[str, Any], **kwds: Any) -> Any:
            return self.owner.wrapper(command, args, kwargs, **kwds)


env_runner = EnvRunner
