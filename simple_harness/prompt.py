"""The input line with prompt_toolkit for proper editing and history."""

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

HISTORY = Path.home() / ".agents" / "history"

STYLE = Style.from_dict({"prompt": "bold #9ece6a"})

bindings = KeyBindings()


@bindings.add("escape", "left")
def _word_left(event):
    document = event.current_buffer.document
    event.current_buffer.cursor_position += (
        document.find_previous_word_beginning(count=1) or 0
    )


@bindings.add("escape", "right")
def _word_right(event):
    document = event.current_buffer.document
    event.current_buffer.cursor_position += (
        document.find_next_word_ending(count=1) or 0
    )


@bindings.add("escape", "enter")
def _newline(event):
    """Option-enter starts a new line instead of sending the message."""
    event.current_buffer.insert_text("\n")


SESSION = None


def read(prompt="> "):
    """Read one message. Raises EOFError on ctrl-d."""
    global SESSION
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        SESSION = PromptSession(
            history=FileHistory(str(HISTORY)),
            key_bindings=bindings,
            style=STYLE,
        )
    return SESSION.prompt(HTML(f" {prompt} "))
