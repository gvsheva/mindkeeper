import shlex
from functools import partial, update_wrapper
from typing import TYPE_CHECKING, Callable, overload

from rich.table import Table

if TYPE_CHECKING:
    from mindkeeper.repl import REPL
else:
    REPL = object


class _CommandWrapper:
    def __init__(self, func: Callable):
        self.func = func
        self.help_fn = None
        self.completions_fn = None

    def __get__(self, obj, *args, **kwargs):
        wrapper = _CommandWrapper(update_wrapper(
            partial(self.func, obj), self.func))
        if self.help_fn is not None:
            wrapper.help_fn = update_wrapper(
                partial(self.help_fn, obj), self.help_fn)
        if self.completions_fn is not None:
            wrapper.completions_fn = update_wrapper(
                partial(self.completions_fn, obj), self.completions_fn)
        return wrapper

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @overload
    def help(self, fn: Callable) -> Callable:
        ...

    @overload
    def help(self) -> str:
        ...

    def help(self, fn: Callable | None = None):
        if fn is not None:
            self.help_fn = fn
            return fn
        if (fn := self.help_fn) is not None:
            return fn()
        return self.func.__doc__

    @overload
    def completions(self, fn: Callable) -> Callable:
        ...

    @overload
    def completions(self) -> dict[str, None] | set[str] | None:
        ...

    def completions(self, fn: Callable | None = None):
        if fn is not None:
            self.completions_fn = fn
            return fn
        if (fn := self.completions_fn) is not None:
            return fn()
        return None


def command(func: Callable):
    return _CommandWrapper(func)


def _is_command(func):
    return isinstance(func, _CommandWrapper)


class Controller:
    _sub_controllers: dict[str, "Controller"]
    _commands: dict[str, _CommandWrapper]

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._sub_controllers = {}
        instance._commands = {}
        for name in dir(instance):
            value = getattr(instance, name)
            if not _is_command(value):
                continue
            command_name = name.replace("_", "-")
            instance._commands[command_name] = value
        return instance

    def add_subcontroller(self, name: str, controller: "Controller"):
        self._sub_controllers[name] = controller

    def execute(self, repl: REPL, text):
        line = shlex.split(text)
        if not line:
            return
        ctrl, *args = line
        if ctrl in self._sub_controllers:
            return self._sub_controllers[ctrl].execute(repl, shlex.join(args))
        if ctrl in self._commands:
            return self._commands[ctrl](repl, *args)
        else:
            print(f"Command not found: {ctrl}")

    def completions(self):
        candidates = {}
        for ctrl in self._sub_controllers:
            candidates[ctrl] = self._sub_controllers[ctrl].completions()
        for name, command in self._commands.items():
            candidates[name] = command.completions()
        return candidates

    @command
    def help(self, repl: REPL, *args):
        """Show help"""
        topic = args[0] if args else None
        if topic is not None and topic in self._sub_controllers:
            return self._sub_controllers[topic].help(repl)
        if topic is not None and topic in self._commands:
            return self._commands[topic].help()
        table = Table(title="Commands")
        table.add_column("Command")
        table.add_column("Description")
        for name, controller in self._sub_controllers.items():
            table.add_row(name, controller.help(repl))
        for name, command in self._commands.items():
            table.add_row(name, command.help())
        return table

    @help.completions
    def _(self):
        return {n: None for n in self._sub_controllers} | {n: None for n in self._commands if n != "help"}


class ApplicationController(Controller):
    pass
