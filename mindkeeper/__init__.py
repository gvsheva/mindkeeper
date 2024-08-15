from argparse import ArgumentParser
from pathlib import Path

from mindkeeper.contacts import ContactsController
from mindkeeper.controller import ApplicationController
from mindkeeper.notes import NotesController
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo


class DirectoryType:
    def __init__(self, mode="r"):
        self.mode = mode

    def __call__(self, path: str):
        p = Path(path)
        if not p.exists():
            raise ValueError(f"{p} does not exist")
        if not p.is_dir():
            raise ValueError(f"{p} is not a directory")
        return p


def run():
    ap = ArgumentParser()
    ap.add_argument(
        "--db-dir",
        type=DirectoryType(),
        default=".",
        help="Database directory")
    ap.add_argument(
        "--db-name",
        type=str,
        default="mindkeeper-db",
        help="Database base name")
    ap.add_argument(
        "--default-prompt",
        type=str,
        default=">>> ",
        help="Default REPL prompt")
    ap.add_argument(
        "--disable-fuzzy-completion",
        action="store_true",
        default=False,
        help="Disable fuzzy completion")

    args = ap.parse_args()

    with Repo(args.db_dir, args.db_name) as repo:
        app = ApplicationController()
        app.add_subcontroller("notes", NotesController(repo))
        app.add_subcontroller("contacts", ContactsController(repo))
        repl = REPL(
            app,
            prompt=args.default_prompt,
            enable_fuzzy_completion=not args.disable_fuzzy_completion,
        )
        repl.run()
