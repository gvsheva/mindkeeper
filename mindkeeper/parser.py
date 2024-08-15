import argparse
from dataclasses import dataclass

from prompt_toolkit.completion import WordCompleter


class CommandArgumentError(ValueError):
    def __init__(self, message: str, help: str):
        super().__init__(message)
        self.help = help


@dataclass(frozen=True)
class CommandArgument:
    name: str
    help: str

    def __str__(self):
        return self.name


class CommandArgumentParser(argparse.ArgumentParser):
    def __init__(self, name):
        super().__init__(
            name,
            prefix_chars="/",
            add_help=False,
            allow_abbrev=False,
            exit_on_error=False,
        )
        self.known_args = set()

    def add_argument(self, name: str, **kwargs):
        super().add_argument(name, **kwargs)
        help = kwargs.get("help", "")
        self.known_args.add(CommandArgument(name, help))

    def error(self, message):
        raise CommandArgumentError(message, self.format_help())

    def completions(self):
        words = []
        display = {}
        for arg in self.known_args:
            if not arg.name.startswith("/"):
                continue
            words.append(arg.name)
            if arg.help:
                display[arg.name] = f"{arg.name}: {arg.help}"
        return WordCompleter(words, display_dict=display)
