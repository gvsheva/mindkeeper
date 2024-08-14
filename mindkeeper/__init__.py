from mindkeeper.contacts import ContactsController
from mindkeeper.controller import ApplicationController
from mindkeeper.notes import NotesController
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo


def run():
    repo = Repo()
    app = ApplicationController()
    app.add_subcontroller("notes", NotesController(repo))
    app.add_subcontroller("contacts", ContactsController())
    repl = REPL(app)
    repl.run()
