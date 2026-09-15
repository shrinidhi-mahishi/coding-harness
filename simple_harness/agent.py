"""The agent loop. This is the main entry point."""

import sys

from . import sandbox
from .compact import compact, needed
from .context import reminder
from .history import estimate, fit, strip, sweep
from .llm import SYSTEM_PROMPT, call_llm
from .prompt import read
from .session import compacted, save
from .tools import TOOL_SCHEMAS, execute
from .ui import ui


def agent_loop(messages):
    """One user turn: call the LLM, run tools, repeat until it stops."""
    while True:
        strip(messages)
        fit(messages)

        with ui.working():
            message, usage = call_llm(messages + [reminder()])

        messages.append(message.model_dump(exclude_none=True))
        ui.usage(usage)

        if message.content:
            ui.agent(message.content)

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        sweep()

        if needed(usage):
            ui.info("compacting context...")
            messages[:] = compact(messages)
            compacted(messages)

    save(messages)


def main():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    ui.banner(sandbox.name())

    while True:
        try:
            user_input = read()
        except (EOFError, KeyboardInterrupt):
            ui.info("\nbye")
            sys.exit(0)

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        agent_loop(messages)


if __name__ == "__main__":
    main()
