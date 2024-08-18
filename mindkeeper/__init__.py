import os
from argparse import ArgumentParser
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings

from mindkeeper.contacts import ContactsController, PhonesController
from mindkeeper.controller import ApplicationController
from mindkeeper.notes import NotesController
from mindkeeper.repl import REPL
from mindkeeper.repo import Repo


class DirectoryType:
    def __call__(self, path: str):
        p = Path(path)
        if not p.exists():
            raise ValueError(f"{p} does not exist")
        if not p.is_dir():
            raise ValueError(f"{p} is not a directory")
        return p

    def __repr__(self):
        return f"{self.__class__.__name__}"


class IntRangeType:
    def __init__(self, min: int, max: int):
        self.min = min
        self.max = max

    def __call__(self, value: str):
        if isinstance(value, int):
            i = value
        else:
            try:
                i = int(value)
            except ValueError:
                raise ValueError(f"{value} is not an integer")
        if not self.min <= i <= self.max:
            raise ValueError(f"{value} is not in range {self.min}..{self.max}")
        return i


class Settings(BaseSettings):
    db_dir: Path = Path(".")
    db_name: str = "mindkeeper-db"
    db_fuzzy_search_ratio: int = 80
    default_prompt: str = ">>> "
    disable_fuzzy_completion: bool = False
    disable_help_on_startup: bool = False
    clear_on_startup: bool = False

    class Config:
        env_prefix = "MINDKEEPER_"


def load_settings():
    values = {
        **dotenv_values(Path.home() / ".mindkeeper.env"),
        **dotenv_values(".env"),
    }
    for k, v in values.items():
        if k.startswith("MINDKEEPER_") and v is not None:
            os.environ[k] = v
    return Settings()


def run():
    settings = load_settings()
    ap = ArgumentParser()
    ap.add_argument(
        "--db-dir",
        type=DirectoryType(),
        default=settings.db_dir,
        help="Database directory",
    )
    ap.add_argument(
        "--db-name",
        type=str,
        default=settings.db_name,
        help="Database base name",
    )
    ap.add_argument(
        "--db-fuzzy-search-ratio",
        type=IntRangeType(0, 100),
        default=settings.db_fuzzy_search_ratio,
        help="Fuzzy search ratio for database queries",
    )
    ap.add_argument(
        "--default-prompt",
        type=str,
        default=settings.default_prompt,
        help="Default REPL prompt",
    )
    ap.add_argument(
        "--disable-fuzzy-completion",
        action="store_true",
        default=settings.disable_fuzzy_completion,
        help="Disable fuzzy completion",
    )
    ap.add_argument(
        "--disable-help-on-startup",
        action="store_true",
        default=settings.disable_help_on_startup,
        help="Disable help on startup",
    )
    ap.add_argument(
        "--clear-on-startup",
        action="store_true",
        default=settings.clear_on_startup,
        help="Clear screen on startup",
    )

    args = ap.parse_args()

    with Repo(
        args.db_dir, args.db_name, fuzzy_search_ratio=args.db_fuzzy_search_ratio
    ) as repo:
        app = ApplicationController()
        app.add_subcontroller("notes", NotesController(repo))
        contacts = ContactsController(repo)
        contacts.add_subcontroller("phones", PhonesController(repo))
        app.add_subcontroller("contacts", contacts)
        repl = REPL(
            app,
            message=args.default_prompt,
            disable_fuzzy_completion=args.disable_fuzzy_completion,
            disable_help_on_startup=args.disable_help_on_startup,
            clear_on_startup=args.clear_on_startup,
        )
        repl.run()
