from mindkeeper.contacts import ContactsController
from mindkeeper.controller import Controller
from mindkeeper.notes import NotesController
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo


def run():
    repo = Repo()
    controller = Controller()
    controller.add_subcontroller("notes", NotesController(repo))
    controller.add_subcontroller("contacts", ContactsController())
    repl = REPL(controller)
    repl.run()
