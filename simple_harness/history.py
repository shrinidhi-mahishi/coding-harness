"""Keeping the transcript small enough to send.

Three mechanisms, cheapest first:
1. cap   — trim a fresh tool result, park full text in a temp file
2. strip — shrink old tool results to stubs after the turn ends
3. drop  — discard whole tool results, oldest first, until it fits
"""

import json
import tempfile
from pathlib import Path

from . import config

CAP = 10_000
STUB = 300

TRIMMED = "[output trimmed:"
SUMMARY = "<summary>"
SPILLS = []


def spill(text):
    """Park the full output on disk for the rest of this turn."""
    handle = tempfile.NamedTemporaryFile(
        mode="w", prefix="simple-harness-", suffix=".txt", delete=False
    )
    handle.write(text)
    handle.close()
    SPILLS.append(Path(handle.name))
    return handle.name


def cap(text):
    """Trim a fresh tool result, leaving a pointer to the whole thing."""
    if len(text) <= CAP:
        return text

    try:
        path = spill(text)
    except OSError:
        return text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} chars cut and the rest could not be saved.]"
    return (
        text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} of {len(text)} chars cut. "
        f"The whole output is at {path} - page through it with "
        "head, tail, sed -n or grep. It is deleted when this turn ends.]"
    )


def sweep():
    """Delete this turn's temp files."""
    for path in SPILLS:
        path.unlink(missing_ok=True)
    SPILLS.clear()


def locked(messages):
    """Length of the frozen prefix."""
    for index in range(len(messages) - 1, -1, -1):
        if SUMMARY in (messages[index].get("content") or ""):
            return index + 1
    return 0


def strip(messages):
    """Shrink every tool result that is no longer part of the live turn."""
    shrunk = 0
    for message in messages[locked(messages):]:
        content = message.get("content") or ""
        if message["role"] != "tool" or TRIMMED in content or len(content) <= STUB:
            continue

        message["content"] = (
            content[:STUB] + f"\n\n{TRIMMED} {len(content) - STUB} more chars. "
            "Run the command again if you need them.]"
        )
        shrunk += 1
    return shrunk


def estimate(messages):
    """Rough token count."""
    return sum(len(json.dumps(m)) for m in messages) // 4


def fit(messages):
    """Last resort: discard whole tool results, oldest first, until it fits."""
    budget = config.CONTEXT_WINDOW * config.COMPACT_AT
    dropped = 0
    for message in messages[locked(messages):]:
        if estimate(messages) <= budget:
            break
        if message["role"] == "tool" and TRIMMED not in (message.get("content") or ""):
            message["content"] = f"{TRIMMED} dropped to fit the context window.]"
            dropped += 1
    return dropped
