from uuid import UUID

from mindkeeper.model import Contact, Note


class Repo:
    def put_note(self, note: Note):
        print(f"Putting note: {note}")

    def get_note(self, id: UUID):
        ...

    def find_notes(self, query: str):
        ...

    def delete_note(self, id: UUID):
        ...
