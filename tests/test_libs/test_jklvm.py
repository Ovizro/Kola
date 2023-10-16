from unittest import TestCase
from kola.klvm import KoiLang, kola_command, kola_text, kola_env_enter, kola_env_exit
from kola.lib.jklvm import JEnvironment, JKoiLang


class JKLTest1(JKoiLang):
    @kola_command
    def restart(self) -> None:
        if self.pc in self._restart_record:
            return
        self._restart_record.add(self.pc)
        self.goto("start")
    
    @kola_command
    def exit(self) -> None:
        super().exit()
    
    @kola_text
    def text(self, text: str) -> str:
        return text
    
    def at_start(self) -> None:
        super().at_start()
        self._restart_record = set()
        self.add_label("start", 0)


class JKLTest2(KoiLang):
    class JEnv1(JEnvironment):
        @kola_env_enter
        def enter(self) -> None:
            self.add_label("enter")
        
        @kola_command
        def goback(self) -> None:
            self.goto("enter")
        
        @kola_env_exit
        def exit(self) -> None:
            pass


class TestJKlvm(TestCase):
    # @skip("old jklvm impl")
    def test_jkoilang(self) -> None:
        string = """
        Hello world!
        #restart

        #exit
        Hello world!
        """
        ret = list(JKLTest1().parse(string, with_ret=True))
        self.assertEqual(ret, ["Hello world!", "Hello world!", None])
