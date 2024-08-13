from mindkeeper.controller import Controller, command
from mindkeeper.model import Note
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo


class NotesController(Controller):
    def __init__(self, repo: Repo):
        self.repo = repo

    @command
    def add(self, repl: REPL, *args: str):
        """Add a note."""
        title, tags, text = "", "", ""
        match args:
            case [title]:
                pass
            case [title, tags]:
                pass
            case [title, tags, text, *_]:
                pass
            case _:
                return "Invalid arguments"
        if not text:
            text = repl.prompt_multiline("Enter note text> ")
        note = Note(title=title, text=text, tags=[
                    t.strip() for t in tags.split(",")])
        self.repo.put_note(note)

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
