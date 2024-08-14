import argparse


class CommandArgumentError(ValueError):
    def __init__(self, message: str, help: str):
        super().__init__(message)
        self.help = help


class CommandArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.known_args = set()

    def add_argument(self, *args, **kwargs):
        super().add_argument(*args, **kwargs)
        for arg in args:
            self.known_args.add(arg)

    def error(self, message):
        raise CommandArgumentError(message, self.format_help())
