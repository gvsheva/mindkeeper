from datetime import datetime
from typing import Sequence

import marko
import marko.block
import marko.element
import marko.inline
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.lexers.markup import MarkdownLexer
from pygments.styles.monokai import MonokaiStyle
from rich.columns import Columns
from rich.markdown import Markdown
from rich.markup import escape
from rich.table import Table

from mindkeeper.controller import Controller, command
from mindkeeper.model import Note
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo
from mindkeeper.utils import format_datetime

_add_parser = CommandArgumentParser("add")
_add_parser.add_argument(
    "/tags", type=str, help="Note tags", nargs="*", default=[])
_add_parser.add_argument(
    "/text", type=str,
    help="Note text (if not provided, will prompt for input)",
    default=None)

_show_parser = CommandArgumentParser("get")
_show_parser.add_argument(
    "id", type=int, help="Note ID")

_edit_parser = CommandArgumentParser("edit")
_edit_parser.add_argument(
    "id", type=int, help="Note ID")
_edit_parser.add_argument(
    "/text", type=str, help="Note text (if not provided, will prompt for input)")
_edit_parser.add_argument(
    "/tags", type=str, help="Note tags", nargs="*", default=[])

_delete_parser = CommandArgumentParser("delete")
_delete_parser.add_argument(
    "id", type=int, help="Note ID")
_delete_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")

_list_parser = CommandArgumentParser("list")
_list_parser.add_argument(
    "/tags", type=str, help="Filter by tags", nargs="*", default=[])
_list_parser.add_argument(
    "/title", type=str, help="Filter by title")
_list_parser.add_argument(
    "/text", type=str, help="Filter by text")
_list_parser.add_argument(
    "/limit", type=int, help="Limit number of notes", default=100)
_list_parser.add_argument(
    "/offset", type=int, help="Offset number of notes", default=0)


_wipe_parser = CommandArgumentParser("wipe")
_wipe_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")


TITLE_MAX_LENGTH = 30


class NotesController(Controller):
    def __init__(self, repo: Repo):
        self.repo = repo

    def _get_title(
            self,
            elem: marko.block.BlockElement | marko.inline.InlineElement | marko.element.Element | Sequence[marko.element.Element] | str,
    ):
        match elem:
            case marko.block.BlockElement() if elem.children:
                return self._get_title(elem.children[0])
            case marko.inline.InlineElement() if elem.children:
                return self._get_title(elem.children)
            case [e, *_]:
                return self._get_title(e)
            case str():
                if len(elem) < TITLE_MAX_LENGTH:
                    return elem
                return elem[:TITLE_MAX_LENGTH - 3] + "..."
            case _:
                return "<untitled>"

    @command
    def add(self, repl: REPL, *args: str):
        """Add a note."""
        parsed = _add_parser.parse_args(args)
        tags, text = parsed.tags, parsed.text
        if text is None:
            lexer = PygmentsLexer(MarkdownLexer)
            style = style_from_pygments_cls(MonokaiStyle)
            text = repl.prompt_multiline(
                "text> ",
                lexer=lexer,
                style=style,
            )
        title = self._get_title(marko.parse(text))
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
        table = Table(title=note.title, show_header=False, expand=True)
        table.add_row(Markdown(note.text))
        table.add_section()
        table.add_row(Columns(
            [f"[green]#{t}[/green]" for t in note.tags],
            equal=True))
        table.add_section()
        table.add_row(f"Created at: {format_datetime(note.created_at)}")
        table.add_row(f"Last modified: {format_datetime(note.updated_at)}")
        return table

    @show.completions
    def _(self):
        return {opt for opt in _show_parser.known_args if opt.startswith("/")}

    @show.help
    def _(self):
        return f"Show a note.\n\n{escape(_show_parser.format_help())}"

    @command
    def edit(self, repl: REPL, *args: str):
        """Edit a note."""
        parsed = _edit_parser.parse_args(args)
        note = self.repo.get_note(parsed.id)
        if note is None:
            return f"Note {parsed.id} not found."
        tags, text = parsed.tags, parsed.text
        note.updated_at = datetime.now()
        if tags:
            note.tags = tags
            self.repo.put_note(note)
            return
        if text is None:
            lexer = PygmentsLexer(MarkdownLexer)
            style = style_from_pygments_cls(MonokaiStyle)
            text = repl.prompt_multiline(
                "text> ",
                default=note.text,
                lexer=lexer,
                style=style,
            )
        title = self._get_title(marko.parse(text))
        note.title = title
        note.text = text
        self.repo.put_note(note)

    @edit.completions
    def _(self):
        return {opt for opt in _edit_parser.known_args if opt.startswith("/")}

    @edit.help
    def _(self):
        return f"Edit a note.\n\n{escape(_edit_parser.format_help())}"

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
        parsed = _list_parser.parse_args(args)
        notes = self.repo.find_notes(
            title=parsed.title,
            text=parsed.text,
            tags=parsed.tags,
            limit=parsed.limit,
            offset=parsed.offset,
        )
        table = Table(title="Notes", expand=True)
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Tags")
        table.add_column("Created at")
        table.add_column("Last modified")
        for note in notes:
            table.add_row(
                str(note.id),
                note.title,
                ", ".join(note.tags),
                format_datetime(note.created_at),
                format_datetime(note.updated_at),
            )
        return table

    @list.completions
    def _(self):
        return {opt for opt in _list_parser.known_args if opt.startswith("/")}

    @list.help
    def _(self):
        return f"List notes.\n\n{escape(_list_parser.format_help())}"

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
