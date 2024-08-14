from mindkeeper.controller import Controller, command
from mindkeeper.model import Note
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo

_add_parser = CommandArgumentParser("add", add_help=False)
_add_parser.add_argument(
    "title", type=str, help="Note title")
_add_parser.add_argument(
    "--tags", type=str, help="Note tags", nargs="*", default=[])
_add_parser.add_argument(
    "--text", type=str, help="Note text", default="")


class NotesController(Controller):
    def __init__(self, repo: Repo):
        self.repo = repo

    @command
    def add(self, repl: REPL, *args: str):
        """Add a note."""
        parsed = _add_parser.parse_args(args)
        title, tags, text = parsed.title, parsed.tags, parsed.text
        if not text:
            text = repl.prompt_multiline("Enter note text> ")
        note = Note(title=title, text=text, tags=tags)
        self.repo.put_note(note)

    @add.completions
    def _(self):
        return {opt for opt in _add_parser.known_args if opt.startswith("-")}

    @add.help
    def _(self):
        return _add_parser.format_help()

    @command
    def delete(self, repl: REPL, *args):
        """Delete a note."""
        if not repl.confirm("Are you sure you want to delete this note?"):
            return
        print(f"Deleting note: {args}")

    @command
    def list(self, repl, *args):
        """List notes."""
        print(f"Listing notes: {args}")

    @command
    def wipe(self, repl, *args):
        """Delete all notes."""
        if not repl.confirm("Are you sure you want to delete all notes?"):
            return
        print("Wiping notes")
