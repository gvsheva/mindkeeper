import shlex
from typing import TYPE_CHECKING, Callable, NamedTuple

from rich.table import Table

if TYPE_CHECKING:
    from mindkeeper.repl import REPL
else:
    REPL = object


class _CommandDecorator:
    def __call__(self, func: Callable):
        func.__annotations__["is_command"] = True
        return func


command = _CommandDecorator()


def _is_command(func):
    return getattr(func, "__annotations__", {}).get("is_command")


class _Command(NamedTuple):
    function: Callable
    help: str


class Controller:
    _sub_controllers: dict[str, "Controller"]
    _commands: dict[str, _Command]

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._sub_controllers = {}
        instance._commands = {}
        for name in dir(instance):
            value = getattr(instance, name)
            if not _is_command(value):
                continue
            command_name = name.replace("_", "-")
            instance._commands[command_name] = _Command(value, value.__doc__)
        return instance

    def add_subcontroller(self, name: str, controller: "Controller"):
        self._sub_controllers[name] = controller

    def execute(self, repl: REPL, text):
        line = shlex.split(text)
        if not line:
            return
        command, *args = line
        if command in self._sub_controllers:
            return self._sub_controllers[command].execute(repl, shlex.join(args))
        if command in self._commands:
            return self._commands[command].function(repl, *args)
        else:
            print(f"Command not found: {command}")

    def completions(self):
        candidates = {}
        for subcontroller in self._sub_controllers:
            candidates[subcontroller] = self._sub_controllers[subcontroller].completions()
        for command in self._commands:
            candidates[command] = None
        candidates["help"] = {
            k for k in self._sub_controllers if k != "help"}
        return candidates

    @command
    def help(self, repl: REPL, *args):
        """Show help"""
        topic = args[0] if args else None
        if topic is not None and topic in self._sub_controllers:
            return self._sub_controllers[topic].help(repl)
        if topic is not None and topic in self._commands:
            return self._commands[topic].help
        table = Table(title="Commands")
        table.add_column("Command")
        table.add_column("Description")
        for name, controller in self._sub_controllers.items():
            table.add_row(name, controller.help(repl))
        for name, command in self._commands.items():
            table.add_row(name, command.help)
        return table
