from typing import TYPE_CHECKING, Literal

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import NestedCompleter
from rich.console import Console

if TYPE_CHECKING:
    from mindkeeper.controller import Controller
else:
    Controller = object


class REPL:
    def __init__(self, controller: Controller, prompt='>>> '):
        self.controller = controller
        self.prompt = prompt

    def _main_toolbart(self):
        return "Press Ctrl+D to exit"

    def _confirm_toolbar(self):
        return "Press y/n to confirm, or Ctrl+C to cancel."

    def _multiline_toolbar(self):
        return "Press Alt+Enter to finish"

    def confirm(self, message: str, default: Literal["N", "Y"] = "N") -> bool:
        while True:
            response = prompt(
                f"{message} (y/n) [{default=}]: ",
                bottom_toolbar=self._confirm_toolbar,
            ).strip().upper()
            if response == "":
                response = default
            if response in ("Y", "N"):
                return response == "Y"
            print("Invalid response. Please enter 'y' or 'n'.")

    def prompt_multiline(self, p: str = ">>> ") -> str:
        return prompt(p, multiline=True, bottom_toolbar=self._multiline_toolbar)

    def run(self):
        console = Console()
        session = PromptSession()
        completer = NestedCompleter.from_nested_dict(
            self.controller.completions())
        console.print(self.controller.help(self))
        while True:
            try:
                text = session.prompt(
                    self.prompt,
                    bottom_toolbar=self._main_toolbart,
                    completer=completer,
                )
                result = self.controller.execute(self, text)
                if result is not None:
                    console.print(result)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print(e)
