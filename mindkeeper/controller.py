import shlex
from functools import partial, update_wrapper
from typing import TYPE_CHECKING, Callable, overload

from prompt_toolkit.completion import Completer, NestedCompleter, WordCompleter
from rich.table import Table
from thefuzz import fuzz

from mindkeeper.utils import CompleterWithDisplay

if TYPE_CHECKING:
    from mindkeeper.repl import REPL
else:
    REPL = object


class _CommandWrapper:
    def __init__(self, func: Callable):
        self.func = func
        self.help_fn = None
        self.short_fn = None
        self.completions_fn = None

    def __get__(self, obj, *args, **kwargs):
        wrapper = _CommandWrapper(update_wrapper(partial(self.func, obj), self.func))
        if self.help_fn is not None:
            wrapper.help_fn = update_wrapper(partial(self.help_fn, obj), self.help_fn)
        if self.short_fn is not None:
            wrapper.short_fn = update_wrapper(
                partial(self.short_fn, obj), self.short_fn
            )
        if self.completions_fn is not None:
            wrapper.completions_fn = update_wrapper(
                partial(self.completions_fn, obj), self.completions_fn
            )
        return wrapper

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    @overload
    def help(self, fn: Callable) -> Callable: ...

    @overload
    def help(self) -> str: ...

    def help(self, fn: Callable | None = None):
        if fn is not None:
            self.help_fn = fn
            return fn
        if (fn := self.help_fn) is not None:
            return fn()
        return self.func.__doc__

    @overload
    def short(self, fn: Callable) -> Callable: ...

    @overload
    def short(self) -> str: ...

    def short(self, fn: Callable | None = None):
        if fn is not None:
            self.short_fn = fn
            return fn
        if (fn := self.short_fn) is not None:
            return fn()
        return self.func.__doc__

    @overload
    def completions(self, fn: Callable[..., Completer]) -> Callable: ...

    @overload
    def completions(self) -> Completer: ...

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
            return self.empty(repl)
        ctrl, *args = line
        if ctrl in self._sub_controllers:
            return self._sub_controllers[ctrl].execute(repl, shlex.join(args))
        if ctrl in self._commands:
            return self._commands[ctrl](repl, *args)
        else:
            return self.default(repl, ctrl, *args)

    def empty(self, repl: REPL):
        return None

    def default(self, repl: REPL, command: str, *args):
        candidates = []
        for candidate in self._sub_controllers:
            rat = fuzz.ratio(candidate, command)
            if rat > 50:
                candidates.append((rat, candidate))
        for candidate in self._commands:
            rat = fuzz.ratio(candidate, command)
            if rat > 50:
                candidates.append((rat, candidate))
        response = f"Command not found: [bold red]'{command}'[/bold red]"
        if candidates:
            candidates.sort(reverse=True)
            candidate = candidates[0][1]
            response += (
                f"\nDid you mean [bold green]'{candidate}'[/bold green]?"  # nopep8
            )
        response += "\nType 'help' for a list of commands."
        return response

    def completions(self) -> Completer:
        nested = {}
        display_dict = {}
        for ctrl in self._sub_controllers:
            nested[ctrl] = self._sub_controllers[ctrl].completions()
            if short := self._sub_controllers[ctrl].short():
                display_dict[ctrl] = f"{ctrl}: {short}"
        for name, command in self._commands.items():
            nested[name] = command.completions()
            if short := command.short():
                display_dict[name] = f"{name}: {short}"
        return CompleterWithDisplay(
            NestedCompleter.from_nested_dict(nested), display_dict
        )

    def short(self):
        return self.__doc__ or ""

    @command
    def help(self, repl: REPL, *args):
        """Show help"""
        topic = args[0] if args else None
        if topic is not None and topic in self._sub_controllers:
            return self._sub_controllers[topic].help(repl)
        if topic is not None and topic in self._commands:
            return self._commands[topic].help()
        table = Table(
            "Command",
            "Description",
            title=self.short() or "Commands",
            show_lines=True,
            expand=True,
        )
        for name, controller in self._sub_controllers.items():
            table.add_row(name, controller.help(repl))
        for name, command in self._commands.items():
            table.add_row(name, command.help())
        return table

    @help.completions
    def _(self):
        words = [n for n in self._sub_controllers] + [
            n for n in self._commands if n != "help"
        ]
        return WordCompleter(words)


class ApplicationExit(Exception):
    pass


class ApplicationController(Controller):
    @command
    def exit(self, repl: REPL, *args):
        """Exit the application."""
        raise ApplicationExit()
