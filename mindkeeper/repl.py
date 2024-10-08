import os
from typing import TYPE_CHECKING, Literal

from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import FuzzyCompleter
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import clear
from pydantic import ValidationError
from rich.console import Console

from mindkeeper.controller import ApplicationExit
from mindkeeper.parser import CommandArgumentError

if TYPE_CHECKING:
    from mindkeeper.controller import Controller
else:
    Controller = object


class REPL:
    def __init__(
        self,
        controller: Controller,
        /,
        message=">>> ",
        disable_fuzzy_completion=True,
        disable_help_on_startup=False,
        clear_on_startup=False,
    ):
        self.controller = controller
        self.message = message
        self.disable_fuzzy_completion = disable_fuzzy_completion
        self.disable_help_on_startup = disable_help_on_startup
        self.clear_on_startup = clear_on_startup
        self.console = Console()

    def _main_toolbart(self):
        return "Press Ctrl+D to exit"

    def _confirm_toolbar(self):
        return "Press y/n to confirm, or Ctrl+C to cancel."

    def _multiline_toolbar(self):
        return "Press Alt+Enter or Esc followed by Enter to finish"

    def confirm(self, message: str, default: Literal["N", "Y"] = "N") -> bool:
        while True:
            response = (
                prompt(
                    f"{message} (y/n) [{default=}]: ",
                    bottom_toolbar=self._confirm_toolbar,
                )
                .strip()
                .upper()
            )
            if response == "":
                response = default
            if response in ("Y", "N"):
                return response == "Y"
            self.console.print("Invalid response. Please enter 'y' or 'n'.")

    def prompt(self, message: AnyFormattedText, **kwargs) -> str:
        if kwargs.get("multiline", False):
            if kwargs.get("bottom_toolbar") is None:
                kwargs["bottom_toolbar"] = self._multiline_toolbar
        try:
            return prompt(message, **kwargs)
        except EOFError:
            return ""

    def run(self):
        history_file = os.environ.get("MINDKEEPER_HISTORY_FILE", ".mindkeeper-history")
        session = PromptSession(history=FileHistory(history_file))
        completer = self.controller.completions()
        if not self.disable_fuzzy_completion:
            completer = FuzzyCompleter(completer)
        if not self.disable_help_on_startup:
            self.console.print(self.controller.help(self))
        if self.clear_on_startup:
            clear()
        while True:
            try:
                text = session.prompt(
                    self.message,
                    bottom_toolbar=self._main_toolbart,
                    completer=completer,
                    auto_suggest=AutoSuggestFromHistory(),
                )
                result = self.controller.execute(self, text)
                if result is not None:
                    self.console.print(result)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except CommandArgumentError as ex:
                self.console.print(ex)
            except ValidationError as ex:
                for error in ex.errors():
                    self.console.print(f"{error['loc'][0]}: {error['msg']}")
            except ApplicationExit:
                break
            except Exception:
                self.console.print_exception()
