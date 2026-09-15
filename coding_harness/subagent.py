"""Subagents: exploration that happens somewhere else.

Four rules:
 1. it starts from an empty history
 2. it holds every tool but two (no recursion, no touching the plan)
 3. it runs the same loop as the main agent
 4. only its last message comes back
"""

import os

MAX_TURNS = 12

WITHHELD = {"task", "write_todos", "str_replace", "write"}

SYSTEM_PROMPT = f"""
You are an exploration subagent. You were given one question by a lead agent
and you answer it. That is the whole job.

You cannot see the conversation that spawned you, and the lead agent cannot
see anything you do here. Only your final message crosses back, so it has to
stand on its own.

You are working in {os.getcwd()}. Search inside it. Never search from / or
from the home directory.

How to work:
- Use bash, read_file and read_skill to find out what is actually true.
- You are here to read and report, not to change anything.
- Search in batches. Several greps in one turn beats one grep per turn.
- Stop as soon as you can answer.

Your final message is the entire report — keep it under 150 words.
Findings only: file paths with line numbers, names, values.
"""


def toolset():
    """Every tool except the ones a guest should not hold."""
    from .tools import TOOL_SCHEMAS

    return [s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD]


def task(description: str) -> str:
    """Run a fresh agent on one question and return only its final answer."""
    from .history import fit
    from .llm import call_llm
    from .tools import execute
    from .ui import ui

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]
    ui.subagent(description)

    report = None

    for _ in range(MAX_TURNS):
        fit(messages)

        with ui.working("subagent exploring"):
            message, usage = call_llm(messages, tools=toolset())

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)
        report = message.content or report

        if not message.tool_calls:
            return report or "(the subagent came back with nothing)"

        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result, nested=True)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    if report:
        return (
            f"(stopped after {MAX_TURNS} turns, before finishing. Partial "
            f"findings below — narrow the question and ask again.)\n\n{report}"
        )
    return f"(stopped after {MAX_TURNS} turns with nothing to report.)"


TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Hand a self-contained exploration question to a fresh agent that "
            "has its own context window, and get back its findings. Use this "
            "to learn how the codebase works. It cannot see this conversation, "
            "so include every detail it needs. It reads and reports; it never edits."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": (
                        "The question, written to stand alone: what to find "
                        "out, where to start looking, and what the answer "
                        "should contain."
                    ),
                }
            },
            "required": ["description"],
        },
    },
}
