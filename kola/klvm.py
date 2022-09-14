from typing import Any, Callable, Dict, Set, Tuple, Union
from types import MethodType
from .lexer import BaseLexer, StringLexer, FileLexer
from .parser import Parser


class KoiLangCommand(object):
    __slots__ = ["__name__", "__func__"]

    def __init__(self, name: str, func: Callable) -> None:
        self.__name__ = name
        self.__func__ = func
    
    def __get__(self, instance: Any, owner: type) -> Callable:
        return self.__func__.__get__(instance, owner)
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__func__(*args, **kwds)


class KoiLangMeta(type):
    """
    Metaclass for KoiLang class
    """
    __command_field__: Set[KoiLangCommand]

    def __new__(cls, name: str, base: Tuple[type, ...], attr: Dict[str, Any]):
        __command_field__ = {i for i in attr.values() if isinstance(i, KoiLangCommand)}
        for i in base:
            if isinstance(i, KoiLangMeta):
                __command_field__.update(i.__command_field__)
        attr["__command_field__"] = __command_field__

        return super().__new__(cls, name, base, attr)
    
    def get_command_set(self, instance: Any) -> Dict[str, MethodType]:
        return {i.__name__: MethodType(i.__func__, instance) for i in self.__command_field__}
    
    
class KoiLang(metaclass=KoiLangMeta):
    """
    Main class for KoiLang parsing.
    """
    __slots__ = ["command_set"]

    def __init__(self) -> None:
        self.command_set = self.__class__.get_command_set(self)

    def __getitem__(self, key: str) -> Callable:
        return self.command_set[key]

    def parse(self, lexer: Union[BaseLexer, str]) -> None:
        if isinstance(lexer, str):
            lexer = StringLexer(lexer)
        Parser(lexer, self.command_set).exec_()
    
    def parse_file(self, path: str) -> None:
        self.parse(FileLexer(path))
    
    def parse_command(self, cmd: str) -> None:
        self.parse(StringLexer(cmd, stat=1))
    
    def parse_args(self, args: str) -> Tuple[tuple, dict]:
        return Parser(StringLexer(args, stat=2), self.command_set).parse_args()


def kola_command(func: Callable[..., Any]) -> KoiLangCommand:
    return KoiLangCommand(func.__name__, func)

def kola_text(func: Callable[[Any, str], Any]) -> KoiLangCommand:
    return KoiLangCommand("@text", func)

def kola_number(func: Callable[..., Any]) -> KoiLangCommand:
    return KoiLangCommand("@number", func)