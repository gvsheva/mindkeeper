from rich.columns import Columns
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table

from mindkeeper.controller import Controller, command
from mindkeeper.model import Note
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo

_add_parser = CommandArgumentParser("add")
_add_parser.add_argument(
    "title", type=str, help="Note title")
_add_parser.add_argument(
    "/tags", type=str, help="Note tags", nargs="*", default=[])
_add_parser.add_argument(
    "/text", type=str,
    help="Note text (if not provided, will prompt for input)",
    default=None)

_show_parser = CommandArgumentParser("get")
_show_parser.add_argument(
    "id", type=int, help="Note ID")

_delete_parser = CommandArgumentParser("delete")
_delete_parser.add_argument(
    "id", type=int, help="Note ID")
_delete_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")

_wipe_parser = CommandArgumentParser("wipe")
_wipe_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")


class NotesController(Controller):
    def __init__(self, repo: Repo):
        self.repo = repo

    @command
    def add(self, repl: REPL, *args: str):
        """Add a note."""
        parsed = _add_parser.parse_args(args)
        title, tags, text = parsed.title, parsed.tags, parsed.text
        if text is None:
            text = repl.prompt_multiline("text> ")
        note = Note(title=title, text=text, tags=tags)
        self.repo.put_note(note)

    @add.completions
    def _(self):
        return {opt for opt in _add_parser.known_args if opt.startswith("/")}

    @add.help
    def _(self):
        return f"Add a note.\n\n{escape(_add_parser.format_help())}"

    @command
    def show(self, repl: REPL, *args: str):
        """Show a note."""
        parsed = _show_parser.parse_args(args)
        note = self.repo.get_note(parsed.id)
        if note is None:
            return f"Note {parsed.id} not found."
        table = Table(title=note.title, show_header=False)
        table.add_row(Markdown(note.text))
        table.add_section()
        table.add_row(Columns(
            [f"[green]#{t}[/green]" for t in note.tags],
            equal=True))
        table.add_section()
        table.add_row(f"Created at: {note.created_at}")
        table.add_row(f"Last modified: {note.updated_at}")
        return table

    @show.completions
    def _(self):
        return {opt for opt in _show_parser.known_args if opt.startswith("/")}

    @show.help
    def _(self):
        return f"Show a note.\n\n{escape(_show_parser.format_help())}"

    @command
    def delete(self, repl: REPL, *args):
        """Delete a note."""
        parsed = _delete_parser.parse_args(args)
        if not (parsed.force or repl.confirm("Are you sure you want to delete")):
            return "Deletion cancelled."
        self.repo.delete_note(parsed.id)

    @delete.completions
    def _(self):
        return {opt for opt in _delete_parser.known_args if opt.startswith("/")}

    @delete.help
    def _(self):
        return f"Delete a note.\n\n{escape(_delete_parser.format_help())}"

    @command
    def list(self, repl, *args):
        """List notes."""
        print(f"Listing notes: {args}")

    @command
    def wipe(self, repl, *args):
        """Delete all notes."""
        parsed = _wipe_parser.parse_args(args)
        if not (parsed.force or repl.confirm("Are you sure you want to delete all notes")):
            return "Wipe cancelled."
        self.repo.wipe_notes()

    @wipe.completions
    def _(self):
        return {opt for opt in _wipe_parser.known_args if opt.startswith("/")}

    @wipe.help
    def _(self):
        return f"Delete all notes.\n\n{escape(_wipe_parser.format_help())}"
