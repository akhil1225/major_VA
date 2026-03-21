# skills/notes_skill.py

import os
from datetime import datetime

DEFAULT_NOTES_FILE = "notes.txt"


def _get_notes_path(base_dir: str | None = None) -> str:
    if base_dir:
        return os.path.join(base_dir, DEFAULT_NOTES_FILE)
    return DEFAULT_NOTES_FILE


def append_note(
    text: str, base_dir: str | None = None, include_timestamp: bool = True
) -> str:
    text = text.strip()
    if not text:
        return "I did not get any text to write in the note."

    path = _get_notes_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None

    with open(path, "a", encoding="utf-8") as f:
        if include_timestamp:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{ts} -> {text}\n")
        else:
            f.write(text + "\n")

    return "Note saved."


def read_notes(base_dir: str | None = None) -> str:
    path = _get_notes_path(base_dir)
    if not os.path.exists(path):
        return "You do not have any saved notes yet."

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return "Your notes file is empty."

    return content
