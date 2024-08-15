from datetime import datetime

from mindkeeper.controller import Controller, command
from mindkeeper.model import Contact, Phone, PhoneType
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.repl import REPL
from mindkeeper.utils import format_datetime

from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.lexers.markup import MarkdownLexer
from pygments.styles.monokai import MonokaiStyle
from rich.table import Table

_add_parser = CommandArgumentParser("add")
_add_parser.add_argument(
    "/name", type=str, help="Friend name", default=None, nargs="*")
_add_parser.add_argument(
    "/phone", type=str,
    help="Phone number (if not provided, will prompt for input)", nargs="*",
    default=None)
_add_parser.add_argument(
    "/birthday", type=str,
    help="birthday like mm.dd (if not provided, will prompt for input)", nargs="*",
    default=None)


class ContactsController(Controller):

    def __init__(self, repo):
        self.repo = repo

    @command
    def add(self, repl: REPL, *args: str):
        """Add a note."""
        parsed = _add_parser.parse_args(args)
        name, phone, birthday = parsed.name, parsed.phone, parsed.birthday
        if name is None:
            lexer = PygmentsLexer(MarkdownLexer)
            style = style_from_pygments_cls(MonokaiStyle)
            name = repl.prompt_multiline(
                "name> ",
                lexer=lexer,
                style=style,
            )


        if phone is None:
            lexer = PygmentsLexer(MarkdownLexer)
            style = style_from_pygments_cls(MonokaiStyle)
            phone = repl.prompt_multiline(
                "phone> ",
                lexer=lexer,
                style=style,
            )

        if birthday is None:
            lexer = PygmentsLexer(MarkdownLexer)
            style = style_from_pygments_cls(MonokaiStyle)
            birthday = repl.prompt_multiline(
                "birthday (mm.dd)> ",
                lexer=lexer,
                style=style,
            )

        bd = datetime.strptime(str(datetime.today().year) + "." + birthday, '%Y.%m.%d')
        contact = Contact(name=name, phones=[Phone(number=phone)], birthday=bd)
        note = self.repo.put_contact(contact)
        return self._format_contact(note)

    @command
    def delete(self, repl, *args):
        """Delete a contact."""
        print(f"Deleting contact: {args}")

    @command
    def list(self, repl, *args):
        """List contacts."""
        print(f"Listing contacts: {args}")

    def _format_contact(self, ct: Contact):
        table = Table(title=ct.name, show_header=False, expand=True)
        table.add_row(f"ID: {ct.id}")
        table.add_row(f"born at: {format_datetime(ct.birthday)}")
        table.add_row(f"phone: {ct.phones}")
        return table
