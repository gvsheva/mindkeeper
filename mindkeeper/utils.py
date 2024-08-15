from datetime import datetime
from typing import Mapping

from prompt_toolkit.completion import CompleteEvent, Completer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import AnyFormattedText, to_formatted_text

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def format_datetime(dt: datetime) -> str:
    return dt.strftime(DATETIME_FORMAT)


class CompleterWithDisplay(Completer):
    def __init__(self, completer: Completer, display_dict: Mapping[str, AnyFormattedText]):
        self.completer = completer
        self.display_dict = display_dict

    def get_completions(self, document: Document, complete_event: CompleteEvent):
        for completion in self.completer.get_completions(document, complete_event):
            display = self.display_dict.get(completion.text, None)
            if display is not None:
                completion.display = to_formatted_text(display)
            yield completion
