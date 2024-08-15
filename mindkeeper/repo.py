import shelve
from enum import StrEnum, auto
from pathlib import Path

from thefuzz import fuzz

from mindkeeper.model import GENERATE, Note


class _INDEXES(StrEnum):
    NOTES = auto()
    CONTACTS = auto()


class Repo:
    data: shelve.Shelf

    def __init__(self, dbdir: Path | str):
        if isinstance(dbdir, str):
            dbdir = Path(dbdir)
        self.dbdir = dbdir

    def open(self):
        self.data = shelve.open(self.dbdir / "mindkeeper-db")

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
            if title and fuzz.partial_ratio(title, note.title) < 80:
                continue
            if text and fuzz.partial_ratio(text, note.text) < 80:
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
