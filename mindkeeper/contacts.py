from datetime import datetime
from rich.markup import escape
from pydantic import ValidationError
from rich.table import Table
from rich.columns import Columns

from mindkeeper.controller import Controller, command
from mindkeeper.repo import Repo
from mindkeeper.repl import REPL
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.model import Contact, Phone
from mindkeeper.utils import format_datetime

_add_parser = CommandArgumentParser("add")
_add_parser.add_argument(
    "/name", type=str,
    help="Contact name (if not provided, will prompt for input)",
    default=None)
_add_parser.add_argument(
    "/address", type=str,
    help="Contact address (if not provided, will prompt for input)",
    default=None)
_add_parser.add_argument(
    "/email", type=str,
    help="Contact email (if not provided, will prompt for input)",
    default=None)
_add_parser.add_argument(
    "/phones", type=str, nargs="+",
    help="Contact phones (if not provided, will prompt for input)",
    default=None)
_add_parser.add_argument(
    "/birthday", type=str,
    help="Contact birthday (if not provided, will prompt for input)",
    default=None)
_add_parser.add_argument(
    "/tags", type=str, help="Contact tags", nargs="*", default=[])

_show_parser = CommandArgumentParser("get")
_show_parser.add_argument(
    "id", type=int, help="Contact ID")

_edit_parser = CommandArgumentParser("edit")
_edit_parser.add_argument(
    "id", type=int, help="Contact ID")
_edit_parser.add_argument(
    "/name", type=str,
    help="Contact name (if not provided, will prompt for input)",
    default=None)
_edit_parser.add_argument(
    "/address", type=str,
    help="Contact address (if not provided, will prompt for input)",
    default=None)
_edit_parser.add_argument(
    "/email", type=str,
    help="Contact email (if not provided, will prompt for input)",
    default=None)
_edit_parser.add_argument(
    "/phones", type=str, nargs="+",
    help="Contact phones (if not provided, will prompt for input)",
    default=None)
_edit_parser.add_argument(
    "/birthday", type=str,
    help="Contact birthday (if not provided, will prompt for input)",
    default=None)
_edit_parser.add_argument(
    "/tags", type=str, help="Contact tags", nargs="*", default=[])
_edit_parser.add_argument(
    "/add-tags", type=str, help="Add tags to note", nargs="*", default=[])
_edit_parser.add_argument(
    "/remove-tags", type=str, help="Remove tags from note", nargs="*", default=[])

_delete_parser = CommandArgumentParser("delete")
_delete_parser.add_argument(
    "id", type=int, help="Contact ID")
_delete_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")

_list_parser = CommandArgumentParser("list")
_list_parser.add_argument(
    "/tags", type=str, help="Filter by tags", nargs="*", default=[])
_list_parser.add_argument(
    "/name", type=str, help="Filter by name")
_list_parser.add_argument(
    "/address", type=str, help="Filter by address")
_list_parser.add_argument(
    "/email", type=str, help="Filter by email")
_list_parser.add_argument(
    "/phone", type=str, help="Filter by phone")
_list_parser.add_argument(
    "/limit", type=int, help="Limit number of contacts", default=100)
_list_parser.add_argument(
    "/offset", type=int, help="Offset number of contacts", default=0)

_wipe_parser = CommandArgumentParser("wipe")
_wipe_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation")


class ContactsController(Controller):
    """A set of commands to manage contacts."""

    def __init__(self, repo: Repo):
        self.repo = repo

    def __format_contact(self, contact: Contact):
        table = Table(title=contact.name, show_header=False, expand=True)
        if contact.tags:
            table.add_row(Columns(
                [f"[green]#{t}[/green]" for t in contact.tags],
                equal=True))
            table.add_section()

        table.add_row(f"ID: {contact.id}")
        table.add_row(f"Name: {contact.name}")
        table.add_row(f"Address: {contact.address or 'N/A'}")
        table.add_row(f"Email: {contact.email or 'N/A'}")
        table.add_row(f"Phones: {', '.join(p.number for p in contact.phones)}")
        table.add_row(f"Birthday: {format_datetime(contact.birthday) if contact.birthday else 'N/A'}")
        return table

    @command
    def add(self, repl: REPL, *args):
        """Add a contact."""
        parsed = _add_parser.parse_args(args)

        name = parsed.name
        if name is None:
            name = repl.prompt("name> ")

        address = parsed.address
        if address is None:
            address = repl.prompt("address> ") or None

        email = parsed.email
        if email is None:
            email = repl.prompt("email> ") or None

        birthday = parsed.birthday
        if birthday is None:
            birthday = repl.prompt("birthday> ") or None

        if birthday is not None:
            try:
                birthday = datetime.strptime(birthday, "%d.%m.%Y")
            except ValueError:
                return "Invalid date format. Use DD.MM.YYYY"

        phones = parsed.phones
        if phones is None:
            phones = []
            phone_counter = 1
            while True:
                phone = repl.prompt(f"phone {phone_counter}> ")
                if phone == "":
                    break
                try:
                    phones.append(Phone(number=phone))
                    phone_counter += 1
                except ValidationError:
                    print("Invalid phone, can start with + and contain 10-15 digits.")
                    continue

        contact = Contact(name=name, address=address, email=email, phones=phones, birthday=birthday)

        contact = self.repo.put_contact(contact)

        return self.__format_contact(contact)

    @add.completions
    def _(self):
        return _add_parser.completions()

    @add.help
    def _(self):
        return f"Add a contact.\n\n{escape(_add_parser.format_help())}"

    @command
    def show(self, repl: REPL, *args: str):
        """Show a note."""
        parsed = _show_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.id)
        if contact is None:
            return f"Contact {parsed.id} not found."
        return self.__format_contact(contact)

    @show.completions
    def _(self):
        return _show_parser.completions()

    @show.help
    def _(self):
        return f"Show a contact.\n\n{escape(_show_parser.format_help())}"

    @command
    def edit(self, repl: REPL, *args):
        """Edit a contact."""
        parsed = _edit_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.id)
        if contact is None:
            return f"Contact {parsed.id} not found."
        update_tags = False

        if parsed.tags:
            contact.tags = parsed.tags
            update_tags = True
        if parsed.add_tags:
            contact.tags = list(set(contact.tags) | set(parsed.add_tags))
            update_tags = True
        if parsed.remove_tags:
            contact.tags = list(set(contact.tags) - set(parsed.remove_tags))
            update_tags = True
        if update_tags:
            contact = self.repo.put_contact(contact)
            return self.__format_contact(contact)

        name = parsed.name
        if name is None:
            name = repl.prompt("name> ", default=contact.name)

        address = parsed.address
        if address is None:
            address = repl.prompt("address> ", default=contact.address or "") or None

        email = parsed.email
        if email is None:
            email = repl.prompt("email> ", default=contact.email or "") or None

        birthday = parsed.birthday
        if birthday is None:
            contact_birthday = contact.birthday.strftime("%d.%m.%Y") if contact.birthday else ""
            birthday = repl.prompt("birthday> ", default=contact_birthday) or None

        if birthday is not None:
            try:
                birthday = datetime.strptime(birthday, "%d.%m.%Y")
            except ValueError:
                return "Invalid date format. Use DD.MM.YYYY"

        edited_phones = parsed.phones or []
        if not edited_phones:
            existing_phones = [p.number for p in contact.phones]
            for i, phone in enumerate(existing_phones, start=1):
                edited_phone = repl.prompt(f"phone {i}> ", default=phone)
                edited_phones.append(Phone(number=edited_phone))

        new_phones = []
        if (repl.confirm("Do you want to add a new phones?", default="N")):
            phone_counter = len(edited_phones) + 1
            while True:
                phone = repl.prompt(f"phone {phone_counter}> ")
                if phone == "":
                    break
                try:
                    new_phones.append(Phone(number=phone))
                    phone_counter += 1
                except ValidationError:
                    print("Invalid phone, can start with + and contain 10-15 digits.")
                    continue

        contact.name = name
        contact.address = address
        contact.email = email
        contact.birthday = birthday
        contact.phones = edited_phones + new_phones

        contact = self.repo.put_contact(contact)
        return self.__format_contact(contact)

    @edit.completions
    def _(self):
        return _edit_parser.completions()

    @edit.help
    def _(self):
        return f"Edit a contact.\n\n{escape(_edit_parser.format_help())}"

    @command
    def delete(self, repl: REPL, *args):
        """Delete a contact."""
        parsed = _delete_parser.parse_args(args)

        if not (parsed.force or repl.confirm("Are you sure you want to delete?")):
            return "Deletion cancelled."

        self.repo.delete_contact(parsed.id)
        return "Contact deleted."

    @delete.completions
    def _(self):
        return _delete_parser.completions()

    @delete.help
    def _(self):
        return f"Delete a contact.\n\n{escape(_delete_parser.format_help())}"

    @command
    def list(self, repl: REPL, *args):
        """List contacts."""
        parsed = _list_parser.parse_args(args)
        contacts = self.repo.find_contacts(
            name=parsed.name,
            address=parsed.address,
            email=parsed.email,
            phone=parsed.phone,
            tags=parsed.tags,
            limit=parsed.limit,
            offset=parsed.offset,
        )
        table = Table(title="Contacts", expand=True)
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Address")
        table.add_column("Email")
        table.add_column("Phones")
        table.add_column("Birthday")
        table.add_column("Tags")
        for contact in contacts:
            table.add_row(
                str(contact.id),
                contact.name,
                contact.address or "N/A",
                contact.email or "N/A",
                ", ".join(p.number for p in contact.phones),
                format_datetime(contact.birthday) if contact.birthday else "N/A",
                ", ".join(contact.tags),
            )
        return table

    @list.completions
    def _(self):
        return _list_parser.completions()

    @list.help
    def _(self):
        return f"List contacts.\n\n{escape(_list_parser.format_help())}"

    @command
    def wipe(self, repl, *args):
        """Delete all notes."""
        parsed = _wipe_parser.parse_args(args)
        if not (parsed.force or repl.confirm("Are you sure you want to delete all contacts")):
            return "Wipe cancelled."
        self.repo.wipe_contacts()

    @wipe.completions
    def _(self):
        return _wipe_parser.completions()

    @wipe.help
    def _(self):
        return f"Delete all contacts.\n\n{escape(_wipe_parser.format_help())}"
