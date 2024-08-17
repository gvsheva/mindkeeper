import shelve
from datetime import datetime, timedelta
from enum import StrEnum, auto
from pathlib import Path

from thefuzz import fuzz

from mindkeeper.model import GENERATE, Contact, Note


class _INDEXES(StrEnum):
    NOTES = auto()
    CONTACTS = auto()


class Repo:
    data: shelve.Shelf

    def __init__(self, dbdir: Path, dbname: str, /, fuzzy_search_ratio=80):
        assert dbdir.is_dir()
        self.dbdir = dbdir
        self.dbname = dbname
        self.fuzzy_search_ratio = fuzzy_search_ratio

    def open(self):
        self.data = shelve.open(self.dbdir / self.dbname)

    def close(self):
        self.data.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _generate_id(self, counter_name: str):
        counter = self.data.get(counter_name, 0)
        counter += 1
        self.data[counter_name] = counter
        return counter

    # ff
    def put_note(self, note: Note):
        if note.id is GENERATE:
            note.id = self._generate_id("__notes_counter")
        index = self.data.get(_INDEXES.NOTES, {})
        index[note.id] = note
        self.data[_INDEXES.NOTES] = index
        return note

    def get_note(self, id: int) -> Note:
        index = self.data.get(_INDEXES.NOTES, {})
        return index.get(id)

    def find_notes(
        self,
        title: str | None = None,
        text: str | None = None,
        tags: list[str] | None = None,
        limit=100,
        offset=0,
    ):
        counter = 0
        for note in self.data.get(_INDEXES.NOTES, {}).values():
            if title:
                r = fuzz.partial_ratio(title, note.title)
                if r < self.fuzzy_search_ratio:
                    continue
            if text:
                r = fuzz.partial_ratio(text, note.text)
                if r < self.fuzzy_search_ratio:
                    continue
            if tags and not set(tags) & set(note.tags):
                continue
            if counter >= offset + limit:
                break
            if counter >= offset:
                yield note
            counter += 1

    def delete_note(self, id: int):
        index = self.data.get(_INDEXES.NOTES, {})
        del index[id]
        self.data[_INDEXES.NOTES] = index

    def wipe_notes(self):
        self.data[_INDEXES.NOTES] = {}
        self.data["__notes_counter"] = 0

    def put_contact(self, contact: Contact):
        if contact.id is GENERATE:
            contact.id = self._generate_id("__contacts_counter")
        index = self.data.get(_INDEXES.CONTACTS, {})
        index[contact.id] = contact
        self.data[_INDEXES.CONTACTS] = index
        return contact

    def get_contact(self, id: int) -> Contact:
        index = self.data.get(_INDEXES.CONTACTS, {})
        return index.get(id)

    def delete_contact(self, id: int):
        index = self.data.get(_INDEXES.CONTACTS, {})
        del index[id]
        self.data[_INDEXES.CONTACTS] = index

    def wipe_contacts(self):
        self.data[_INDEXES.CONTACTS] = {}
        self.data["__contacts_counter"] = 0

    def find_contacts(
        self,
        name: str | None = None,
        address: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        tags: list[str] | None = None,
        was_born_in_next_n_days: int | None = None,
        limit=100,
        offset=0,
    ):
        counter = 0
        for contact in self.data.get(_INDEXES.CONTACTS, {}).values():
            if name:
                r = fuzz.partial_ratio(name, contact.name)
                if r < self.fuzzy_search_ratio:
                    continue
            if address:
                r = fuzz.partial_ratio(address, contact.address)
                if r < self.fuzzy_search_ratio:
                    continue
            if email:
                r = fuzz.partial_ratio(email, contact.email)
                if r < self.fuzzy_search_ratio:
                    continue
            if phone:
                if not contact.phones:
                    continue
                found = False
                for i in contact.phones:
                    r = fuzz.partial_ratio(phone, i.number)
                    if r < self.fuzzy_search_ratio:
                        continue
                    else:
                        found = True
                        break
                if not found:
                    continue
            if was_born_in_next_n_days is not None:
                if contact.birthday is None:
                    continue
                dolim = datetime.today()
                uplim = dolim + timedelta(days=was_born_in_next_n_days)
                dmd = (dolim.year, dolim.month, dolim.day)
                umd = (uplim.year, uplim.month, uplim.day)
                md = (dolim.year, contact.birthday.month, contact.birthday.day)
                if not (dmd <= md <= umd):
                    continue
            if tags and not set(tags) & set(contact.tags):
                continue
            if counter >= offset + limit:
                break
            if counter >= offset:
                yield contact
            counter += 1
