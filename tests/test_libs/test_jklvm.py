from unittest import TestCase, skip
from kola.klvm import CommandSet, KoiLang, kola_command, kola_text
from kola.lib.jklvm import JEnvironment, JKoiLang


class JKLvmTest1(JKoiLang):
    @kola_command
    def restart(self) -> None:
        if self.pc in self._restart_record:
            return
        self._restart_record.add(self.pc)
        self.goto("@start")
    
    @kola_command
    def exit(self) -> None:
        super().exit()
    
    @kola_text
    def text(self, text: str) -> str:
        return text
    
    def at_start(self) -> None:
        super().at_start()
        self._restart_record = set()
        self.add_label("@start", 0)


class TestJKlvm(TestCase):
    # @skip("old jklvm impl")
    def test_jkoilang(self) -> None:
        string = """
        Hello world!
        #restart

        #exit
        Hello world!
        """
        ret = list(JKLvmTest1().parse(string, with_ret=True))
        self.assertEqual(ret, ["Hello world!", "Hello world!", None])
