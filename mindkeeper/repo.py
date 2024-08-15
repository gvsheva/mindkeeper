from enum import StrEnum, auto

from mindkeeper.model import GENERATE, Note


class _INDEXES(StrEnum):
    NOTES = auto()
    CONTACTS = auto()


class Repo:
    def __init__(self):
        self.data = {}

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

    def get_note(self, id: int) -> Note:
        index = self.data.get(_INDEXES.NOTES, {})
        return index.get(id)

    def find_notes(self, query: str):
        ...

    def delete_note(self, id: int):
        index = self.data.get(_INDEXES.NOTES, {})
        del index[id]
        self.data[_INDEXES.NOTES] = index

    def wipe_notes(self):
        self.data[_INDEXES.NOTES] = {}
        self.data["__notes_counter"] = 0
