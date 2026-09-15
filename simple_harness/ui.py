"""Console output with Rich."""

from contextlib import contextmanager

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax


class UI:
    def __init__(self):
        self.console = Console()

    def banner(self, sandbox_name):
        self.console.print(
            Panel(
                f"[bold green]simple-harness[/] — a minimal coding agent\n"
                f"sandbox: [cyan]{sandbox_name}[/]  •  ctrl-d to quit",
                border_style="dim",
            )
        )

    def agent(self, text):
        self.console.print(Markdown(text))

    def tool(self, name, args, result, nested=False):
        prefix = "  ↳" if nested else "⚙"
        arg_summary = ", ".join(f"{k}={repr(v)[:60]}" for k, v in args.items())
        self.console.print(f"[dim]{prefix} {name}({arg_summary})[/]")

        if result and len(result) < 800:
            self.console.print(Panel(result, border_style="dim", expand=False))

    def user_denied(self, reason):
        self.console.print(f"[yellow]⊘ denied:[/] {reason}")

    def subagent(self, description):
        self.console.print(
            Panel(
                f"[italic]{description}[/]",
                title="[cyan]subagent[/]",
                border_style="cyan",
                expand=False,
            )
        )

    def usage(self, usage):
        parts = [f"prompt={usage['prompt_tokens']}", f"gen={usage['completion_tokens']}"]
        if usage.get("reasoning_tokens"):
            parts.append(f"reasoning={usage['reasoning_tokens']}")
        if usage.get("cached_tokens"):
            parts.append(f"cached={usage['cached_tokens']}")
        self.console.print(f"[dim]  tokens: {', '.join(parts)}[/]")

    def info(self, text):
        self.console.print(f"[dim]{text}[/]")

    def error(self, text):
        self.console.print(f"[red]{text}[/]")

    def approve(self, description):
        self.console.print(f"\n[yellow]? {description}[/]")
        try:
            answer = input("  allow? [y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in ("y", "yes", "")

    @contextmanager
    def working(self, label="thinking"):
        with Live(Spinner("dots", text=label), console=self.console, transient=True):
            yield


ui = UI()
