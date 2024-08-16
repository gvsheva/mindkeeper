from datetime import datetime
from typing import Literal

from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError as PromptValidationError
from prompt_toolkit.validation import Validator
from pydantic import EmailStr, TypeAdapter, ValidationError
from rich.columns import Columns
from rich.markup import escape
from rich.table import Table

from mindkeeper.controller import Controller, command
from mindkeeper.model import Contact, Phone, PhoneNumber, PhoneType
from mindkeeper.parser import CommandArgumentParser
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo
from mindkeeper.utils import format_datetime

_add_parser = CommandArgumentParser("add")
_add_parser.add_argument(
    "/name",
    type=str,
    help="Contact name (if not provided, will prompt for input)",
    default=None,
)
_add_parser.add_argument(
    "/address",
    type=str,
    help="Contact address (if not provided, will prompt for input)",
    default=None,
)
_add_parser.add_argument(
    "/email",
    type=str,
    help="Contact email (if not provided, will prompt for input)",
    default=None,
)
_add_parser.add_argument(
    "/phones",
    type=str,
    nargs="+",
    help="Contact phones (if not provided, will prompt for input)",
    default=None,
)
_add_parser.add_argument(
    "/birthday",
    type=str,
    help="Contact birthday (if not provided, will prompt for input)",
    default=None,
)
_add_parser.add_argument("/tags", type=str, help="Contact tags", nargs="*", default=[])

_show_parser = CommandArgumentParser("get")
_show_parser.add_argument("id", type=int, help="Contact ID")

_edit_parser = CommandArgumentParser("edit")
_edit_parser.add_argument("id", type=int, help="Contact ID")
_edit_parser.add_argument(
    "/name",
    type=str,
    help="Contact name (if not provided, will prompt for input)",
    default=None,
)
_edit_parser.add_argument(
    "/address",
    type=str,
    help="Contact address (if not provided, will prompt for input)",
    default=None,
)
_edit_parser.add_argument(
    "/email",
    type=str,
    help="Contact email (if not provided, will prompt for input)",
    default=None,
)
_edit_parser.add_argument(
    "/birthday",
    type=str,
    help="Contact birthday (if not provided, will prompt for input)",
    default=None,
)
_edit_parser.add_argument("/tags", type=str, help="Contact tags", nargs="*", default=[])
_edit_parser.add_argument(
    "/add-tags", type=str, help="Add tags to note", nargs="*", default=[]
)
_edit_parser.add_argument(
    "/remove-tags", type=str, help="Remove tags from note", nargs="*", default=[]
)

_delete_parser = CommandArgumentParser("delete")
_delete_parser.add_argument("id", type=int, help="Contact ID")
_delete_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation"
)

_list_parser = CommandArgumentParser("list")
_list_parser.add_argument(
    "/tags", type=str, help="Filter by tags", nargs="*", default=[]
)
_list_parser.add_argument("/name", type=str, help="Filter by name")
_list_parser.add_argument("/address", type=str, help="Filter by address")
_list_parser.add_argument("/email", type=str, help="Filter by email")
_list_parser.add_argument("/phone", type=str, help="Filter by phone")
_list_parser.add_argument(
    "/limit", type=int, help="Limit number of contacts", default=100
)
_list_parser.add_argument(
    "/offset", type=int, help="Offset number of contacts", default=0
)

_wipe_parser = CommandArgumentParser("wipe")
_wipe_parser.add_argument(
    "/force", action="store_true", help="Force deletion without confirmation"
)


class _PhoneValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text
        if text.strip() == "":
            return
        try:
            TypeAdapter(PhoneNumber).validate_python(text)
        except ValidationError:
            raise PromptValidationError(message="invalid phone number")


class _EmailValidator(Validator):
    def validate(self, document: Document) -> None:
        text = document.text
        if text.strip() == "":
            return
        try:
            TypeAdapter(EmailStr).validate_python(text)
        except ValidationError:
            raise PromptValidationError(message="invalid email")


class _DateValidator(Validator):
    def __init__(self, format: str):
        self.format = format

    def validate(self, document: Document) -> None:
        text = document.text
        if text.strip() == "":
            return
        try:
            datetime.strptime(text, self.format)
        except ValueError:
            raise PromptValidationError(
                message=f"invalid date format, should be {self.format}"
            )


BIRTHDAY_FORMAT = "%d.%m.%Y"


class ContactsController(Controller):
    """A set of commands to manage contacts."""

    def __init__(self, repo: Repo):
        self.repo = repo

    def _format_contact(self, contact: Contact):
        table = Table(title=contact.name, show_header=False, expand=True)
        if contact.tags:
            table.add_row(
                Columns([f"[green]#{t}[/green]" for t in contact.tags], equal=True)
            )
            table.add_section()

        table.add_row(f"ID: {contact.id}")
        table.add_row(f"Name: {contact.name}")
        table.add_row(f"Address: {contact.address or 'N/A'}")
        table.add_row(f"Email: {contact.email or 'N/A'}")
        table.add_row(f"Phones: {', '.join(p.number for p in contact.phones)}")
        table.add_row(
            f"Birthday: {format_datetime(contact.birthday) if contact.birthday else 'N/A'}"
        )
        return table

    def _ask_name(self, repl: REPL, current: str = "") -> str | Literal[False]:
        while True:
            name = repl.prompt("name> ", default=current).strip()
            if not name:
                if repl.confirm("Name is required. Do you want to cancel?", "Y"):
                    return False
            else:
                return name

    def _ask_address(self, repl: REPL, current: str = "") -> str | None:
        return repl.prompt("address> ", default=current).strip() or None

    def _ask_email(self, repl: REPL, current: str = "") -> str | None:
        return (
            repl.prompt("email> ", default=current, validator=_EmailValidator()).strip()
            or None
        )

    def _ask_birthday(
        self, repl: REPL, current: datetime | None = None
    ) -> datetime | None:
        if current is not None:
            default = current.strftime(BIRTHDAY_FORMAT)
        else:
            default = ""
        birthday = (
            repl.prompt(
                "birthday> ", default=default, validate=_DateValidator(BIRTHDAY_FORMAT)
            ).strip()
            or None
        )
        if birthday is not None:
            birthday = datetime.strptime(birthday, BIRTHDAY_FORMAT)
        return birthday

    @command
    def add(self, repl: REPL, *args):
        """Add a contact."""
        parsed = _add_parser.parse_args(args)

        name = parsed.name
        if name is None:
            match self._ask_name(repl):
                case False:
                    return "Cancelled."
                case name:
                    pass

        address = parsed.address
        if address is None:
            address = self._ask_address(repl)

        email = parsed.email
        if email is None:
            email = self._ask_email(repl)

        birthday = parsed.birthday
        if birthday is None:
            birthday = self._ask_birthday(repl)

        phones = parsed.phones
        if phones is None:
            phones = []
            phone_counter = 1
            while True:
                phone = repl.prompt(
                    f"phone {phone_counter}> ", validator=_PhoneValidator()
                )
                if phone.strip() == "":
                    break
                phones.append(Phone(number=phone))
                phone_counter += 1

        contact = Contact(
            name=name, address=address, email=email, phones=phones, birthday=birthday
        )

        contact = self.repo.put_contact(contact)

        return self._format_contact(contact)

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
        return self._format_contact(contact)

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
            return self._format_contact(contact)

        name = parsed.name
        if name is None:
            match self._ask_name(repl, contact.name):
                case False:
                    return "Cancelled."
                case name:
                    pass

        address = parsed.address
        if address is None:
            address = self._ask_address(repl, contact.address or "")

        email = parsed.email
        if email is None:
            email = self._ask_email(repl, contact.email or "")

        birthday = parsed.birthday
        if birthday is None:
            birthday = self._ask_birthday(repl, contact.birthday)

        contact.name = name
        contact.address = address
        contact.email = email
        contact.birthday = birthday

        contact = self.repo.put_contact(contact)
        return self._format_contact(contact)

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
        if not (
            parsed.force or repl.confirm("Are you sure you want to delete all contacts")
        ):
            return "Wipe cancelled."
        self.repo.wipe_contacts()

    @wipe.completions
    def _(self):
        return _wipe_parser.completions()

    @wipe.help
    def _(self):
        return f"Delete all contacts.\n\n{escape(_wipe_parser.format_help())}"


_add_phone_parser = CommandArgumentParser("add")
_add_phone_parser.add_argument("contact_id", type=int, help="Contact ID")
_add_phone_parser.add_argument("number", type=str, help="Phone number")
_add_phone_parser.add_argument(
    "/type",
    type=PhoneType,
    help="Phone type (mobile, work, home)",
    choices=[e.name.lower() for e in PhoneType],
    default="mobile",
)

_edit_phone_parser = CommandArgumentParser("edit")
_edit_phone_parser.add_argument("contact_id", type=int, help="Contact ID")
_edit_phone_parser.add_argument("idx", type=int, help="Phone index")
_edit_phone_parser.add_argument("/number", type=str, default=None, help="Phone number")
_edit_phone_parser.add_argument(
    "/type",
    type=PhoneType,
    help="Phone type (mobile, work, home)",
    choices=[e.name.lower() for e in PhoneType],
    default=None,
)

_delete_phone_parser = CommandArgumentParser("delete")
_delete_phone_parser.add_argument("contact_id", type=int, help="Contact ID")
_delete_phone_parser.add_argument("idx", type=int, help="Phone index")

_list_phones_parser = CommandArgumentParser("list")
_list_phones_parser.add_argument("contact_id", type=int, help="Contact ID")


class PhonesController(Controller):
    """ "A set of commands to manage phones."""

    def __init__(self, repo: Repo):
        self.repo = repo

    @command
    def add(self, repl: REPL, *args):
        """Add a phone to a contact."""
        parsed = _add_phone_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.contact_id)
        if contact is None:
            return f"Contact {parsed.contact_id} not found."
        phone = Phone(number=parsed.number, type=parsed.type)
        contact.phones.append(phone)
        self.repo.put_contact(contact)
        return f"Phone added to {contact.name}."

    @add.completions
    def _(self):
        return _add_phone_parser.completions()

    @add.help
    def _(self):
        return f"Add a phone to a contact.\n\n{escape(_add_phone_parser.format_help())}"

    @command
    def edit(self, repl: REPL, *args):
        """Edit a phone of a contact."""
        parsed = _edit_phone_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.contact_id)
        if contact is None:
            return f"Contact {parsed.contact_id} not found."
        try:
            phone = contact.phones[parsed.idx]
        except IndexError:
            return f"Phone {parsed.idx} not found."
        if parsed.number is not None:
            phone.number = parsed.number
        if parsed.type is not None:
            phone.type = parsed.type
        self.repo.put_contact(contact)
        return f"Phone {parsed.idx} edited."

    @edit.completions
    def _(self):
        return _edit_phone_parser.completions()

    @edit.help
    def _(self):
        return (
            f"Edit a phone of a contact.\n\n{escape(_edit_phone_parser.format_help())}"
        )

    @command
    def delete(self, repl: REPL, *args):
        """Delete a phone of a contact."""
        parsed = _delete_phone_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.contact_id)
        if contact is None:
            return f"Contact {parsed.contact_id} not found."
        try:
            del contact.phones[parsed.idx]
        except IndexError:
            return f"Phone {parsed.idx} not found."
        self.repo.put_contact(contact)
        return f"Phone {parsed.idx} deleted."

    @delete.completions
    def _(self):
        return _delete_phone_parser.completions()

    @delete.help
    def _(self):
        return f"Delete a phone of a contact.\n\n{escape(_delete_phone_parser.format_help())}"

    @command
    def list(self, repl: REPL, *args):
        """List phones of a contact."""
        parsed = _list_phones_parser.parse_args(args)
        contact = self.repo.get_contact(parsed.contact_id)
        if contact is None:
            return f"Contact {parsed.contact_id} not found."
        table = Table(title=f"Phones of {contact.name}", expand=True)
        table.add_column("Index")
        table.add_column("Number")
        table.add_column("Type")
        for i, phone in enumerate(contact.phones):
            table.add_row(str(i), phone.number, phone.type.name)
        return table

    @list.completions
    def _(self):
        return _list_phones_parser.completions()

    @list.help
    def _(self):
        return (
            f"List phones of a contact.\n\n{escape(_list_phones_parser.format_help())}"
        )
